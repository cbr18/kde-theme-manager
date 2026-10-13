import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami

Kirigami.AbstractCard {
    id: card
    Layout.preferredWidth: 160
    Layout.minimumWidth: 140
    Layout.maximumWidth: 200
    contentItem: ColumnLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing

        // Radio button + icon
        RowLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter
            spacing: Kirigami.Units.smallSpacing

            Kirigami.Icon {
                source: "preferences-desktop-theme"
                Layout.preferredWidth: 32
                Layout.preferredHeight: 32
                color: isActive ? Kirigami.Theme.highlightColor : Kirigami.Theme.textColor
                opacity: isActive ? 1.0 : 0.5
            }

            Kirigami.RadioButton {
                id: radio
                checked: isActive
                text: profileName === "glass" ? i18n("Glass") :
                      profileName === "paper" ? i18n("Paper") : profileName
                onClicked: {
                    if (!isActive) {
                        clicked()
                    }
                }
            }
        }

        // Component count badge
        Label {
            Layout.alignment: Qt.AlignHCenter
            text: i18n("%1 components", componentCount)
            font.pointSize: Kirigami.Units.fontSizes.small
            color: Kirigami.Theme.textColor
            opacity: 0.6
        }
    }

    // Properties
    property string profileName: ""
    property bool isActive: false
    property int componentCount: 0

    // Signal
    signal clicked()

    // Visual feedback
    background: Rectangle {
        implicitWidth: 160
        implicitHeight: 80
        radius: Kirigami.Units.largeRadius
        border.color: isActive ? Kirigami.Theme.highlightColor : Kirigami.Theme.viewColor
        border.width: isActive ? 2 : 1
        color: isActive ? Kirigami.Theme.highlightColor : "transparent"
        opacity: isActive ? 0.1 : 1.0

        Behavior on border.color { ColorAnimation { duration: 200 } }
        Behavior on color { ColorAnimation { duration: 200 } }
        Behavior on opacity { NumberAnimation { duration: 200 } }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onEntered: parent.border.color = isActive ? Kirigami.Theme.highlightColor : Kirigami.Theme.hoverColor
        onExited: parent.border.color = isActive ? Kirigami.Theme.highlightColor : Kirigami.Theme.viewColor
    }
}