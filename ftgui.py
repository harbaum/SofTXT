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

    def open(self):
        pass

    def is_open(self):
        return True

    def set_attr(self, item, str):
        if fttxt2_gui_connector.app:
            fttxt2_gui_connector.app.set_attr(item, str)
            
    def get_attr(self, item):
        if fttxt2_gui_connector.app:
            return fttxt2_gui_connector.app.get_attr(item)
    
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
        
