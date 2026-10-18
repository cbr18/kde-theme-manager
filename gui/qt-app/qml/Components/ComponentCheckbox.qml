import QtQuick
import org.kde.kirigami.platform as Platform
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami

Kirigami.AbstractCard {
    id: checkbox

    // Fallback colors for PySide6 bundled Qt
    function safeColor(role, fallback) {
        var c = Kirigami.Theme[role]
        return c && c.valid ? c : fallback
    }

    Layout.fillWidth: true
    property string componentId: ""
    property string componentName: ""
    property string componentStatus: ""
    property string componentStatusText: ""
    property string componentDescription: ""
    property string componentIcon: ""
    property bool componentSupportsLiveReload: false
    property bool isSelected: false
    property bool isAvailable: false
    property bool glassMode: false

    readonly property color fgColor: glassMode ? "#ffffff" : safeColor("textColor", "#1f1f1f")
    readonly property color dimColor: glassMode ? Qt.rgba(1, 1, 1, 0.6) : Qt.rgba(0.15, 0.15, 0.15, 0.6)
    readonly property color disabledColor: glassMode ? Qt.rgba(1, 1, 1, 0.45) : safeColor("disabledTextColor", "#888888")

    // Visual state
    property color statusColor: {
        switch (componentStatus) {
            case "available": return safeColor("positiveTextColor", "#27ae60")
            case "partial": return safeColor("warningTextColor", "#f39c12")
            case "not_installed": return safeColor("negativeTextColor", "#e74c3c")
        }
        return dimColor
    }

    signal toggled(bool checked, string componentId)

    contentItem: RowLayout {
        spacing: Platform.Units.mediumSpacing

        // Checkbox
        Kirigami.CheckBox {
            checked: checkbox.isSelected
            enabled: checkbox.isAvailable
            onToggled: checkbox.toggled(checked, checkbox.componentId)
            Layout.alignment: Qt.AlignVCenter
            palette.windowText: checkbox.fgColor
            palette.text: checkbox.fgColor
        }

        // Icon
        Kirigami.Icon {
            source: checkbox.componentIcon
            Layout.preferredWidth: Platform.Units.iconSizes.medium
            Layout.preferredHeight: Platform.Units.iconSizes.medium
            color: checkbox.isAvailable ? checkbox.fgColor : checkbox.disabledColor
            opacity: checkbox.isAvailable ? 1.0 : 0.5
        }

        // Name + status
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            RowLayout {
                Label {
                    text: checkbox.componentName
                    font.bold: true
                    color: checkbox.isAvailable ? checkbox.fgColor : checkbox.disabledColor
                }

                Label {
                    text: checkbox.componentStatusText
                    font.pointSize: Platform.Units.smallSpacing
                    color: checkbox.statusColor
                    visible: !checkbox.isAvailable || checkbox.componentStatus === "partial"
                }

                Label {
                    text: qsTr("Live")
                    font.pointSize: Platform.Units.smallSpacing
                    color: checkbox.safeColor("highlightColor", "#2980b9")
                    visible: checkbox.componentSupportsLiveReload && checkbox.isAvailable
                }
            }

            Label {
                text: checkbox.componentDescription
                font.pointSize: Platform.Units.smallSpacing
                color: checkbox.dimColor
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                visible: checkbox.componentDescription !== ""
            }
        }
    }

    background: Rectangle {
        radius: 4
        color: checkbox.glassMode ? Qt.rgba(1, 1, 1, 0.06) : checkbox.safeColor("viewColor", "#ffffff")
    }
}
