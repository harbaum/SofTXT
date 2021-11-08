import QtQuick 2.9
import QtQuick.Window 2.3
import QtQuick.Templates 2.2 as T
import QtQuick.Controls.Material 2.2

T.ApplicationWindow {
    id: win
    signal execScript (string script, bool ret)
    signal execResultStr (string result)
    signal execResultBool (bool result)
    
    onExecScript: {
	  // run script and return result if requested
	  var retval = eval(script)
	  if(ret) {
		  if(typeof(retval) == "boolean")
		    	  win.execResultBool(retval)
		  else
		    	  win.execResultStr(retval)
	  }
    }

    visible: true
    width: 240
    height: 230
    color: "#ff0000"
}
