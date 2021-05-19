#
# ftgui.py
#
# simple ftgui stub class for ROBO Pro Coding
#

import threading, time

class fttxt2_gui_connector:
    app = None   # will be overwritten by main app
    
    def __init__(self, name):
        if not fttxt2_gui_connector.app:
            print("ERROR: no app registered");

    def run(self):
        pass

    def running(self):
        # return if the gui is still running
        # TODO: fix this
        return True
    
    def checkbox_toggled(self, cbox, handler):
        if fttxt2_gui_connector.app:
            fttxt2_gui_connector.app.install_handler(cbox, "checkbox_toggled", handler)
        
    def slider_moved(self, slider, handler):
        if fttxt2_gui_connector.app:
            fttxt2_gui_connector.app.install_handler(slider, "slider_moved", handler)

    def button_clicked(self, btn, handler):
        if fttxt2_gui_connector.app:
            fttxt2_gui_connector.app.install_handler(btn, "button_clicked", handler)
            
    def switch_toggled(self, sw, handler):
        if fttxt2_gui_connector.app:
            fttxt2_gui_connector.app.install_handler(sw, "switch_toggled", handler)
            
    def input_accepted(self, inp, handler):
        if fttxt2_gui_connector.app:
            fttxt2_gui_connector.app.install_handler(inp, "input_accepted", handler)
        
    def exec_script(self, script):
        if fttxt2_gui_connector.app:
            fttxt2_gui_connector.app.execScript(script)
