import QtQuick 2.9
import QtQuick.Window 2.3
import QtQuick.Templates 2.2 as T
import QtQuick.Controls.Material 2.2

T.ApplicationWindow {
    signal execScript (string script)
    
    onExecScript: eval(script)

    visible: true
    width: 240
    height: 230
    color: "#ff0000"
}
