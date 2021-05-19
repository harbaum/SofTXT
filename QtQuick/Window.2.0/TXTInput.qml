import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Controls.impl 2.12
import QtQuick.Templates 2.12 as T

Item {
   id: root
   property int elide
   property alias text: control.text
   property alias color: control.color
   property alias label1: control
   property font font
   signal onEvent(string msg, string parm)

   TextField {
     id: control
     onAccepted: root.onEvent(root.objectName+":input_accepted", "text:"+control.text)     
     verticalAlignment: TextInput.AlignVCenter
     font.pixelSize: root.font.pixelSize * 0.62
     width: root.width
     height: root.height
   }
   Rectangle {
     border.width: 1
     color: "#eeeeee"
     border.color: "#000000"
  }
}
