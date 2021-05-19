import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Controls.impl 2.12
import QtQuick.Templates 2.12 as T

T.Slider {
    id: control

    padding: 6

    signal onEvent(string msg, string state)
    onMoved: control.onEvent(control.objectName+":slider_moved", "value:"+Math.round(control.value))

    handle: Rectangle {
        x: control.leftPadding + (control.horizontal ? control.visualPosition * (control.availableWidth - width) : (control.availableWidth - width) / 2)
        y: control.topPadding + (control.horizontal ? (control.availableHeight - height) / 2 : control.visualPosition * (control.availableHeight - height))
        width: control.horizontal ? 10 : 28
        height: control.horizontal ? 28 : 10
        radius: (control.horizontal ? width : height ) / 2
        color: "#1984F3"
    }

    background: Rectangle {
        x: control.leftPadding + (control.horizontal ? 0 : (control.availableWidth - width) / 2)
        y: control.topPadding + (control.horizontal ? (control.availableHeight - height) / 2 : 0)
        implicitWidth: control.horizontal ? 200 : 12
        implicitHeight: control.horizontal ? 12 : 200
        width: control.horizontal ? control.availableWidth : implicitWidth
        height: control.horizontal ? implicitHeight : control.availableHeight
        radius: 1
        scale: control.horizontal && control.mirrored ? -1 : 1
        border.width: 1
        border.color: "#1984F3"

        Rectangle {
            y: control.horizontal ? 0 : control.visualPosition * parent.height
            width: control.horizontal ? control.position * parent.width : 12
            height: control.horizontal ? 12 : control.position * parent.height

            color: "#1984F3"
        }
    }
}
