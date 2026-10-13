import QtQuick
import org.kde.kirigami.platform as Platform
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami

Kirigami.AbstractCard {
    id: card
    Layout.preferredWidth: 160
    Layout.minimumWidth: 140
    Layout.maximumWidth: 200
    property string profileName: ""
    property bool isActive: false
    property int componentCount: 0

    signal profileClicked(string profileName)

    contentItem: ColumnLayout {
        Layout.fillWidth: true
        spacing: Platform.Units.smallSpacing

        RowLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter
            spacing: Platform.Units.smallSpacing

            Kirigami.Icon {
                source: "preferences-desktop-theme"
                Layout.preferredWidth: 32
                Layout.preferredHeight: 32
                color: isActive ? Kirigami.Theme.highlightColor : Kirigami.Theme.textColor
                opacity: isActive ? 1.0 : 0.5
            }

            RadioButton {
                id: radio
                checked: isActive
                text: profileName === "glass" ? qsTr("Glass") :
                      profileName === "paper" ? qsTr("Paper") : profileName
                enabled: enabled
                onClicked: {
                    if (!isActive && enabled) {
                        profileClicked(profileName)
                    }
                }
            }
        }

        Label {
            Layout.alignment: Qt.AlignHCenter
            text: qsTr("%1 components").arg(componentCount)
            font.pointSize: Platform.Units.smallSpacing
            color: Kirigami.Theme.textColor
            opacity: 0.6
        }
    }

    background: Rectangle {
        id: bgRect
        implicitWidth: 160
        implicitHeight: 80
        radius: Platform.Units.largeRadius
        border.width: isActive ? 2 : 1
        color: "transparent"
        opacity: 1.0

        Behavior on border.color { ColorAnimation { duration: 200 } }
        Behavior on color { ColorAnimation { duration: 200 } }
        Behavior on opacity { NumberAnimation { duration: 200 } }
    }

    // Update background properties when theme/state changes
    Binding {
        target: bgRect
        property: "radius"
        value: Platform.Units.largeRadius
    }
    Binding {
        target: bgRect
        property: "border.color"
        value: isActive ? Kirigami.Theme.highlightColor : (enabled ? Kirigami.Theme.viewColor : Kirigami.Theme.disabledTextColor)
    }
    Binding {
        target: bgRect
        property: "color"
        value: isActive ? Kirigami.Theme.highlightColor : "transparent"
    }
    Binding {
        target: bgRect
        property: "opacity"
        value: isActive ? 0.1 : (enabled ? 1.0 : 0.5)
    }
    Binding {
        target: bgRect
        property: "border.width"
        value: isActive ? 2 : 1
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        enabled: enabled
        onEntered: if (enabled) bgRect.border.color = isActive ? Kirigami.Theme.highlightColor : Kirigami.Theme.hoverColor
        onExited: if (enabled) bgRect.border.color = isActive ? Kirigami.Theme.highlightColor : Kirigami.Theme.viewColor
    }
}