import QtQuick
import org.kde.kirigami.platform as Platform
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami

Kirigami.AbstractCard {
    id: card

    // Fallback colors for PySide6 bundled Qt
    function safeColor(role, fallback) {
        var c = Kirigami.Theme[role]
        return c && c.valid ? c : fallback
    }

    Layout.preferredWidth: 180
    Layout.minimumWidth: 150
    Layout.maximumWidth: 240

    property string profileName: ""
    // isActive: profile currently applied to the system
    property bool isActive: false
    // selected: profile the user picked (not applied yet)
    property bool selected: false
    property int componentCount: 0
    property bool glassMode: false

    readonly property string displayName: profileName === "glass" ? qsTr("Glass")
        : profileName === "paper" ? qsTr("Paper")
        : profileName

    readonly property color accentColor: safeColor("highlightColor", "#3daee9")
    readonly property color positiveColor: safeColor("positiveTextColor", "#27ae60")
    readonly property color fgColor: glassMode ? "#f0f0f0" : safeColor("textColor", "#1f1f1f")
    readonly property color dimColor: glassMode ? Qt.rgba(1, 1, 1, 0.80) : Qt.rgba(0.15, 0.15, 0.15, 0.65)

    signal profileClicked(string profileName)

    contentItem: ColumnLayout {
        spacing: 2

        RowLayout {
            Layout.fillWidth: true
            spacing: Platform.Units.smallSpacing

            RadioButton {
                Layout.fillWidth: true
                checked: card.isActive || card.selected
                enabled: card.enabled
                text: card.displayName
                font.bold: card.isActive
                onClicked: card.profileClicked(card.profileName)
                palette.windowText: card.fgColor
                palette.text: card.fgColor
            }

            Kirigami.Icon {
                visible: card.isActive
                source: "dialog-ok-apply"
                color: card.positiveColor
                Layout.preferredWidth: 18
                Layout.preferredHeight: 18
                Layout.alignment: Qt.AlignVCenter
            }
        }

        Label {
            Layout.leftMargin: Platform.Units.gridUnit * 1.6
            text: qsTr("%1 components").arg(card.componentCount)
            font.pointSize: Platform.Units.smallSpacing
            color: card.dimColor
        }

        Label {
            Layout.leftMargin: Platform.Units.gridUnit * 1.6
            visible: card.isActive
            text: qsTr("Active now")
            font.pointSize: Platform.Units.smallSpacing
            color: card.positiveColor
        }

        Label {
            Layout.leftMargin: Platform.Units.gridUnit * 1.6
            visible: !card.isActive && card.selected
            text: qsTr("Press Apply to use")
            font.pointSize: Platform.Units.smallSpacing
            color: card.accentColor
        }
    }

    background: Rectangle {
        radius: 8
        implicitWidth: 180
        implicitHeight: 96
        border.width: (card.isActive || card.selected) ? 2 : 1
        border.color: card.isActive ? card.positiveColor
            : card.selected ? card.accentColor
            : (card.glassMode ? Qt.rgba(1, 1, 1, 0.22) : Qt.rgba(0.15, 0.15, 0.15, 0.22))
        color: card.isActive ? Qt.rgba(card.positiveColor.r, card.positiveColor.g, card.positiveColor.b, 0.16)
            : card.selected ? Qt.rgba(card.accentColor.r, card.accentColor.g, card.accentColor.b, 0.16)
            : (card.glassMode ? Qt.rgba(1, 1, 1, 0.06) : "transparent")

        Behavior on border.color { ColorAnimation { duration: 150 } }
        Behavior on color { ColorAnimation { duration: 150 } }
    }
}
