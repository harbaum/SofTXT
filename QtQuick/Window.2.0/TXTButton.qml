import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Controls.impl 2.12
import QtQuick.Templates 2.12 as T

T.Button {
    id: control
    
    signal onEvent(string msg, string state)
    onClicked: control.onEvent(control.objectName+":button_clicked", undefined)

    contentItem: Text {
        text: control.text
	font.pixelSize: control.font.pixelSize * 0.62
	color: "#ffffff"
	horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        color: control.down?"#707070":"#909090"
    }
}
