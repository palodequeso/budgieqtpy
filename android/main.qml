import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    visible: true
    width: 360
    height: 640
    title: "Budgie"
    color: "#f0f0f0"

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 20

        Text {
            id: titleText
            text: "Budgie — Running on Android"
            font.pixelSize: 24
            color: "#333333"
            Layout.alignment: Qt.AlignHCenter
        }

        Button {
            id: pingButton
            text: "Test Python Bridge"
            Layout.alignment: Qt.AlignHCenter
            onClicked: {
                var response = bridge.ping()
                resultText.text = response
            }
        }

        Text {
            id: resultText
            text: ""
            font.pixelSize: 16
            color: "#007700"
            wrapMode: Text.Wrap
            Layout.alignment: Qt.AlignHCenter
            Layout.maximumWidth: 300
        }
    }
}
