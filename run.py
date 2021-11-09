#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# run.py
#
# This program takes a txt project name as parameter and tries
# to run it.
#
# Currently supported are:
# - Display (interpret display.qml and run display.py)
# - Controller
#   - Switch inputs
#   - photo resistor inputs
#   - LED outputs
# - Execution of main python code

# TODO:
# - use semaphore instead of queue
#
#

from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtCore import QThread, QObject, QTimer, pyqtSignal, pyqtSlot
import sys, os, time, queue, select
import json

# fischertechnik seems to have placed their own custom
# widgets in one of the standard modules which they import
# Dirty hack: We add a local QtQuick/Window.2.0 to place
# our objects there to not mess with the qt installation

import ftgui
from fischertechnik.control.VoiceControl import VoiceControl

class AppRunnerThread(QThread):
    finished = pyqtSignal()
    
    def __init__(self, app): 
        super(AppRunnerThread,self).__init__()
        print("Run:", app.split("/")[-1]);

        # load app code
        with open(app, "r") as f:
            self.code = f.read()

    def run(self):
        # run if there's code
        if self.code:
            exec(self.code, {})
        
        self.finished.emit()
            
class RunApplication(QApplication):
    doExecScript = pyqtSignal(str, bool)

    # handle user triggered gui events (e.g. "Wenn Schieberegler bewegt)"
    def handler(self, eid, parm):
        # parm has the form "item:state" if present
        event = { }
        # expected event parameter: "value", "checked", "text"
        if parm:
            name,val = parm.split(":")
            # make "checked" a bool ...
            if name == "checked":
                val = val == "true"                
            # ... and "value" an int
            if name == "value":
                val = int(val)
                
            event[name] = val
               
        if eid in self.handlers:
            self.handlers[eid](event)
        else:
            print("No such handler:", eid)
            
    def install_handler(self, id, event, handler):
        # set object name, so it's addressable from the python side
        self.doExecScript.emit(id+".objectName = \""+id+"\"", False);
        # it may take some time for this to show effect
        obj = None
        while not obj: obj = self.engine.rootObjects()[0].findChild(QObject, id)

        self.handlers[id+":"+event] = handler
        obj.onEvent.connect(self.handler)        
        
    def execScript(self, code):
        self.doExecScript.emit(code, False)

    # this is also new
    def set_attr(self, item, value):
        # RP-C converts everything to a string. How do we know if it's
        # actually a string?        
        if value == "true" or value == "false":
            self.doExecScript.emit(item + "= "+str(value)+"", False);
        else:
            self.doExecScript.emit(item + "= \""+value+"\"", False);

    def get_attr(self, item):
        # simply invoke attribute name. This will return its value
        self.doExecScript.emit(item, True);

        # wait for result
        while self.queue.empty(): pass

        # return result
        return self.queue.get()
        
    def openProject(self):
        # try to open project file
        with open(self.path + ".project.json") as f:
            self.project = json.load(f)
            print("Name:", self.project["name"])
            print("Mode:", self.project["mode"])
            print("UUid:", self.project["uuid"])

            # if display code is present, then run it
            self.runDisplay()
            self.runApp()

    def runApp(self):
        # make sure app code finds its local imports
        sys.path.append(self.path)

        # run background thread for main program itself
        self.thread = AppRunnerThread(self.path + self.project["name"]+".py")
        self.thread.start()

    def execResult(self, str):
        self.queue.put(str)            
        
    def runDisplay(self):
        qml = os.path.join(self.path, "lib/display.qml")
        if not os.path.isfile(qml):
            print("No display.qml file")
            return

        self.engine = QQmlApplicationEngine()
        self.engine.addImportPath(os.path.dirname(os.path.realpath(__file__)))
        self.engine.load(qml)

        win = self.engine.rootObjects()[0]
        if len(self.path.split("/")) >= 2:
            win.setTitle(self.path.split("/")[-2])
        
        self.doExecScript.connect(win.execScript)
        win.execResultStr.connect(self.execResult)
        win.execResultBool.connect(self.execResult)

        # check if something was loaded
        return bool(self.engine.rootObjects())

    def on_timer(self):
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            try:
                line = sys.stdin.readline()
            except:
                line = None
                
            data = None
            if line:
                # whatever we are reading here is supposed to be json encoded
                # and since we are reading a full line it
                # xyz
                try:
                    data = json.loads(line)
                except:
                    # ignore any malformed json input
                    pass

            if data:
                # currently only remote commands are supported
                if "remote" in data:
                    for listener in  VoiceControl.listeners:
                        listener(data["remote"])

    def __init__(self, args):
        QApplication.__init__(self, args)

        self.handlers = { }

        # create a timer to periodically check stdin for input
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(10)

        # queue to pass attribute results from the gui into the app
        self.queue = queue.Queue()

        # register self with gui connector
        ftgui.fttxt2_gui_connector.app = self
        
        # get project name
        self.path = os.path.dirname(os.path.realpath(__file__))+"/workspaces/"+args[1]+"/"

        self.openProject()
        self.exec_()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Please provide a project name");
        sys.exit(-1)
    
    RunApplication(sys.argv)
    sys.exit(0)

