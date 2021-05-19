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

from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
import sys, os, time
import json

# fischertechnik seems to have placed their own custom
# widgets in one of the standard modules which they import
# Dirty hack: We add a local QtQuick/Window.2.0 to place
# our objects there to not mess with the qt installation

import ftgui

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
    doExecScript = pyqtSignal(str)

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
        self.doExecScript.emit(id+".objectName = \""+id+"\"");
        # it may take some time for this to show effect
        obj = None
        while not obj: obj = self.engine.rootObjects()[0].findChild(QObject, id)

        self.handlers[id+":"+event] = handler
        obj.onEvent.connect(self.handler)        
        
    def execScript(self, code):
        self.doExecScript.emit(code)
        
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
        
    def runDisplay(self):
        qml = os.path.join(self.path, "lib/display.qml")
        if not os.path.isfile(qml):
            print("No display.qml file")
            return

        self.engine = QQmlApplicationEngine()
        self.engine.addImportPath(os.path.dirname(os.path.realpath(__file__)))
        self.engine.load(qml)

        win = self.engine.rootObjects()[0]
        self.doExecScript.connect(win.execScript)
        
        # check if something was loaded
        return bool(self.engine.rootObjects())
    
    def __init__(self, args):
        QApplication.__init__(self, args)

        self.handlers = { }
        
        # register self with gui connector
        ftgui.fttxt2_gui_connector.app = self
        
        # get project name
        self.path = os.path.dirname(os.path.realpath(__file__))+"/workspaces/"+args[1]+"/"

        self.openProject()
        self.exec_()

if __name__ == "__main__":
    RunApplication(sys.argv)

