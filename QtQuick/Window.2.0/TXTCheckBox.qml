import QtQuick 2.12
import QtQuick.Templates 2.12 as T
import QtQuick.Controls 2.12
import QtQuick.Controls.impl 2.12

T.CheckBox {
    id: control

    padding: 6
    spacing: 6

    signal onEvent(string msg, string state)
    onToggled: control.onEvent(control.objectName+":checkbox_toggled", "checked:"+control.checked)

    // keep in sync with CheckDelegate.qml (shared CheckIndicator.qml was removed for performance reasons)
    indicator: Rectangle {
        implicitWidth: 20
        implicitHeight: 20

	

        x: control.leftPadding
        y: control.topPadding + (control.availableHeight - height) / 2

        color: "transparent"
        border.width: 2
        border.color: "#ffffff"

        ColorImage {
            x: (parent.width - width) / 2
            y: (parent.height - height) / 2
            defaultColor: "#353637"
            color: "#ffffff"
            source: "qrc:/qt-project.org/imports/QtQuick/Controls.2/images/check.png"
            visible: control.checkState === Qt.Checked
        }

        Rectangle {
            x: (parent.width - width) / 2
            y: (parent.height - height) / 2
            width: 16
            height: 3
            color: control.palette.text
            visible: control.checkState === Qt.PartiallyChecked
        }
    }

    contentItem: CheckLabel {
        leftPadding: control.indicator && !control.mirrored ? control.indicator.width + control.spacing : 0
        rightPadding: control.indicator && control.mirrored ? control.indicator.width + control.spacing : 0

        text: control.text
        font.pixelSize: control.font.pixelSize * 0.62
        color: "#ffffff"
    }
}
