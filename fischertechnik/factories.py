#
# factories.py - ftDuino interface and factory API 
#

import threading, time

import serial, json, select
import serial.tools.list_ports

from fischertechnik.controller.Motor import Motor

FTDUINO_VIDPID = "1c40:0538"
POLL_DELAY = .1  # poll inputs every 100ms for "Starte jedes mal" blocks

# this in fact does not implement a TXT but an ftDuino ...
class ftduino():
    def __init__(self, ext = None):
        if ext != None:
            # later we might search for multiple ftDuino's
            print("WARNING: Ignoring request for extension controller")
            return
        
        # search for ftDuino on USB
        ports = []
        self.lock = threading.Lock()
            
        for p in serial.tools.list_ports.grep("vid:pid="+FTDUINO_VIDPID):
                ports.append(p.device)

        self.ftduino = None
        self.input_values = { }
    
        if len(ports) == 0:
            print("No ftDuino found");
            self.ftduino = None
            return
        
        # try to connect ...
        try:
            # The Serial object that the printer is communicating on.
            self.ftduino = serial.Serial(ports[0], 19200, timeout=3)
        except serial.serialutil.SerialException:
            print("Error connecting to ftDuino");

    def get_loudspeaker(self):
        return loudspeaker()
            
    def set_o_value(self, port, val):
        val = (val * 255)//512        
        cmd = { "set": { "port": "o"+str(port), "value": val, "mode": "high" } }
        self.lock.acquire()
        self.send(json.dumps(cmd))
        self.lock.release()

    def set_m_value(self, port, val, mode):
        val = (val * 255)//512        
        cmd = { "set": { "port": "m"+str(port), "value": val, "mode": mode } }
        self.lock.acquire()
        self.send(json.dumps(cmd))
        self.lock.release()

    def set_i_mode(self, port, mode):
        cmd = { "set": { "port": "i"+str(port), "mode": mode } }
        if "i"+str(port) in self.input_values:
            self.input_values.pop("i"+str(port))  # clear any old value
        self.lock.acquire()
        self.send(json.dumps(cmd))        
        self.lock.release()

    def poll(self, port):
        if not self.ftduino: return None
            
        # read all available bytes from ftduino
        r = [ 1 ]
        msg = ""
        while len(r):            
            r, w, e = select.select([self.ftduino], [], [self.ftduino], 1)
            if not self.ftduino in r:
                print("Decoding timeout");
                return None
                
            # append character
            msg += self.ftduino.read().decode()
            
            # check for a full decodable message
            try:
                msg = json.loads(msg)
                if "port" in msg and "value" in msg and msg["port"].lower() == port:
                    return msg["value"]
                else:
                    None  # decodable but not the info we were hoping for
            except:
                pass
                
        return None
        
    def get_i_value(self, port):
        port = "i"+str(port)        
        cmd = { "get": { "port": port } }
        self.lock.acquire()
        self.send(json.dumps(cmd))
        val = self.poll(port);
        self.lock.release()
        return val
        
    def send(self, cmd):
        if self.ftduino:
            self.ftduino.write(cmd.encode())

####################### CONTROLLER FACTORY ####################
def init_controller_factory():
    pass

class controller_factory():
    def create_graphical_controller(ext = None):
        return ftduino(ext)

########## root device inherited by all device types ##########
    
class device():
    def __init__(self):
        self.listeners = { }
    
    def add_change_listener(self, action, listener):
        print("add_change_listener({}, \"{}\", {})".format(self.name(), action, listener))
        self.listeners[action] = listener

    def runListener(self, action):
        if action in self.listeners:
            self.listeners[action]()
        
    def name(self):
        return type(self).__name__

####################### LOUDSPEAKER ####################
class loudspeaker(device):
    # no need to implement anything since the ftDuino
    # has no speaker
    pass

####################### OUTPUT FACTORY ####################
def init_output_factory():
    pass

class output():
    def __init__(self, controller, port):
        super().__init__()
        self.controller = controller
        self.port = port

    def set(self, val):
        self.controller.set_o_value(self.port, val);
        
class led(output):
    def __init__(self, controller, port):
        super().__init__(controller, port)

    def set_brightness(self, val):
        self.set(val)
    
class output_factory():
    def create_led(controller, port):
        return led(controller, port)

####################### MOTOR FACTORY ####################
def init_motor_factory():
    pass

class motor(device):
    def __init__(self, controller, port):
        super().__init__()
        self.controller = controller
        self.port = port

        self.val = 0
        self.dir = Motor.CW

    def set_speed(self, val, dir):
        self.dir = dir
        self.cal = val

    def start(self):
        self.controller.set_m_value(self.port, self.val, "right" if self.dir ==  Motor.CW else "left" )
        
    def stop(self):
        self.controller.set_m_value(self.port, 0, "brake");
        
    def coast(self):
        self.controller.set_m_value(self.port, 0, "open");
        
class encodermotor(motor):
    def __init__(self, controller, port):
        super().__init__(controller, port)

class motor_factory():
    def create_motor(controller, port):
        return motor(controller, port)

    def create_encodermotor(controller, port):
        return encodermotor(controller, port)

####################### INPUT FACTORY ####################
def init_input_factory():
    pass

class input(device):
    thread = None  # single global thread for all inputs
    handler = [ ]
    
    def __init__(self, controller, port):
        super().__init__()
        self.controller = controller
        self.port = port

    def get_value(self):
        return self.controller.get_i_value(self.port)
    
    def input_monitor(self):
        while True:
            # poll inputs
            for h in input.handler:
                value = self.controller.get_i_value(h["obj"].port)
                if value != None and value != h["value"]:
                    h["value"] = value
                    h["handler"](value)
                    
            time.sleep(POLL_DELAY)
        
    def add_change_listener(self, ref, callback):
        print("ref", ref)
        # create background task if we don't have one yet
        if not input.thread:
            input.thread = threading.Thread(target=self.input_monitor, daemon=True)
            input.thread.start()

        # store listener in handler list
        input.handler.append( { "obj": self, "ref": ref, "handler": callback,
                                "value": self.controller.get_i_value(self.port) } )
            
class input_switch(input):
    def __init__(self, controller, port):
        super().__init__(controller, port)
        controller.set_i_mode(port, "switch")

    def get_state(self):
        return self.get_value()
    
class input_resistance(input):
    def __init__(self, controller, port):
        super().__init__(controller, port)
        controller.set_i_mode(port, "resistance")

    def get_resistance(self):
        return self.get_value()
    
class input_voltage(input):
    def __init__(self, controller, port):
        super().__init__(controller, port)
        controller.set_i_mode(port, "voltage")

    def get_voltage(self):
        return self.get_value()
    
class mini_switch(input_switch):
    def is_open(self):
        return self.get_value()

    def is_closed(self):
        return not self.get_value()
        
class photo_resistor(input_resistance):
    pass
        
class photo_transistor(input_switch):
    def is_dark(self):
        return self.get_value()
    
    def is_bright(self):
        return not self.get_value()

class ntc_resistor(input_resistance):
    pass

class color_sensor(input_voltage):
    pass
        
class trail_follower(input_voltage):
    pass

class ultrasonic_distance_meter(input):
    def __init__(self, controller, port):
        super().__init__(controller, port)

    def get_distance(self):
        return 0

class input_factory():
    def create_mini_switch(controller, port):
        return mini_switch(controller, port)

    def create_photo_resistor(controller, port):
        return photo_resistor(controller, port)
    
    def create_photo_transistor(controller, port):
        return photo_transistor(controller, port)

    def create_ultrasonic_distance_meter(controller, port):
        return ultrasonic_distance_meter(controller, port)

    def create_ntc_resistor(controller, port):
        return ntc_resistor(controller, port)

    def create_color_sensor(controller, port):
        return color_sensor(controller, port)
    
    def create_trail_follower(controller, port):
        return trail_follower(controller, port)

# recently added ...    
def init():
    pass

def initialized():
    return True
    
# todo: run a background process that talks to the ftduino
