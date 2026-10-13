import QtQuick
import org.kde.kirigami.platform as Platform
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami

Kirigami.AbstractCard {
    id: checkbox
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
            case "available": return Kirigami.Theme.positiveTextColor
            case "partial": return Kirigami.Theme.warningTextColor
            case "not_installed": return Kirigami.Theme.negativeTextColor
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
            color: isAvailable ? Kirigami.Theme.textColor : Kirigami.Theme.disabledTextColor
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
                    color: isAvailable ? Kirigami.Theme.textColor : Kirigami.Theme.disabledTextColor
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
                    color: Kirigami.Theme.highlightColor
                    visible: componentSupportsLiveReload && isAvailable
                }
            }

            Label {
                text: componentDescription
                font.pointSize: Platform.Units.smallSpacing
                color: Kirigami.Theme.textColor
                opacity: 0.6
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                visible: componentDescription !== ""
            }
        }
    }

    // Disabled overlay
    Rectangle {
        id: disabledOverlay
        anchors.fill: parent
        color: Kirigami.Theme.viewColor
        opacity: isAvailable ? 0 : 0.15
        visible: !isAvailable
    }

    signal toggled(bool checked, string componentId)
}