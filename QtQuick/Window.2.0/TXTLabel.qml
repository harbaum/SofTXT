import QtQuick 2.9
import QtQuick.Controls 2.2
import QtQuick.Controls.impl 2.2
import QtQuick.Templates 2.2 as T

Item {
   id: root
   property alias elide: control.elide
   property alias text: control.text
   property alias color: control.color
   property font font

   Label {
        id: control
	color: "#ffffff"
	font.pixelSize: root.font.pixelSize * 0.62
	y: (root.height - height) / 2
    }
}
