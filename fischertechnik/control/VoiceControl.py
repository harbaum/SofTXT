# fischertechnik.control.VoiceControl
class VoiceControl():
    listeners = [ ]

    def add_command_listener(self, cb):
        # simply store all command listeners in list
        VoiceControl.listeners.append(cb)
