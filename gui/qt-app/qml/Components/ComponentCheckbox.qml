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

    // Visual state
    property color statusColor: {
        switch (componentStatus) {
            case "available": return safeColor("positiveTextColor", "#27ae60")
            case "partial": return safeColor("warningTextColor", "#f39c12")
            case "not_installed": return safeColor("negativeTextColor", "#e74c3c")
        }
    }

    contentItem: RowLayout {
        Layout.fillWidth: true
        spacing: Platform.Units.mediumSpacing

        // Checkbox
        Kirigami.CheckBox {
            id: check
            checked: isSelected
            enabled: isAvailable
            onToggled: checkbox.toggled(checked, componentId)
            Layout.alignment: Qt.AlignVCenter
        }

        // Icon
        Kirigami.Icon {
            source: componentIcon
            Layout.preferredWidth: Platform.Units.iconSizes.medium
            Layout.preferredHeight: Platform.Units.iconSizes.medium
            color: isAvailable ? safeColor("textColor", "#1f1f1f") : safeColor("disabledTextColor", "#888888")
            opacity: isAvailable ? 1.0 : 0.5
        }

        // Name + status
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            RowLayout {
                Label {
                    text: componentName
                    font.bold: true
                    color: isAvailable ? safeColor("textColor", "#1f1f1f") : safeColor("disabledTextColor", "#888888")
                }

                // Status badge
                Label {
                    text: componentStatusText
                    font.pointSize: Platform.Units.smallSpacing
                    color: statusColor
                    visible: !isAvailable || componentStatus === "partial"
                }

                // Live reload badge
                Label {
                    text: i18n("Live")
                    font.pointSize: Platform.Units.smallSpacing
                    color: safeColor("highlightColor", "#2980b9")
                    visible: componentSupportsLiveReload && isAvailable
                }
            }

            Label {
                text: componentDescription
                font.pointSize: Platform.Units.smallSpacing
                color: safeColor("textColor", "#1f1f1f")
                opacity: 0.6
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                visible: componentDescription !== ""
            }
        }
    }

    // Disabled overlay
    background: Rectangle {
        color: glassMode ? "transparent" : safeColor("viewColor", "#e0e0e0")
        radius: 4
    }

    Rectangle {
        id: disabledOverlay
        anchors.fill: parent
        color: safeColor("viewColor", "#e0e0e0")
        opacity: isAvailable ? 0 : 0.15
        visible: !isAvailable
    }

    signal toggled(bool checked, string componentId)
}