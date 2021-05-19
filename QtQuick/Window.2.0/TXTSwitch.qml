import QtQuick 2.12
import QtQuick.Templates 2.12 as T
import QtQuick.Controls 2.12
import QtQuick.Controls.impl 2.12

T.Switch {
    id: control
    
    signal onEvent(string msg, string parm)
    onToggled: control.onEvent(control.objectName+":switch_toggled", "checked:"+control.checked)

    padding: 6
    spacing: 6

    indicator: PaddedRectangle {
    	width: 40
        height: 20

        x: control.leftPadding
        y: control.topPadding + (control.availableHeight - height) / 2

        radius: 11
        leftPadding: 0
        rightPadding: 0
        padding: (height - 20) / 2
        color: "transparent"
     	border.color: "#ffffff"
	border.width: 2

        Rectangle {
            x: Math.max(7, Math.min(parent.width - width - 7, control.visualPosition * parent.width - (width / 2)))
            y: (parent.height - height) / 2
            width: 8
            height: 8
            radius: 4
            color: "#ffffff"

            Behavior on x {
                enabled: !control.down
                SmoothedAnimation { velocity: 200 }
            }
        }
    }

    contentItem: CheckLabel {
        leftPadding: control.indicator.width + control.spacing

        text: control.text
        font.pixelSize: control.font.pixelSize * 0.62
        color: "#ffffff"
    }
}
