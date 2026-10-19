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
    property bool glassMode: false

    // Visual state
    readonly property color statusColor: {
        switch (componentStatus) {
            case "available": return ThemeColors.positive()
            case "partial": return ThemeColors.warning()
            case "not_installed": return ThemeColors.negative()
        }
        return ThemeColors.dimColor(glassMode)
    }

    // Present the status in the UI language. `componentStatusText` comes from the
    // Python model, which returns its own (Russian) wording, so it is only used
    // as a fallback for a status this component does not know.
    readonly property string statusLabel: {
        switch (componentStatus) {
            case "available": return qsTr("Installed")
            case "partial": return qsTr("Partial")
            case "not_installed": return qsTr("Not installed")
        }
        return componentStatusText
    }

    // Named `componentToggled` because AbstractCard inherits ItemDelegate →
    // AbstractButton, which already declares `toggled()` — re-declaring it
    // is a fatal "duplicate signal name" error.
    signal componentToggled(bool checked, string componentId)

    contentItem: RowLayout {
        spacing: Platform.Units.mediumSpacing

        // Checkbox (Kirigami has no CheckBox type; QQC2's is what it would alias)
        CheckBox {
            id: box
            checked: checkbox.isSelected
            // QQC2 writes to `checked` on toggle, which destroys the binding
            // above. Re-arm it so the model stays authoritative.
            Binding {
                target: box
                property: "checked"
                value: checkbox.isSelected
                restoreMode: Binding.RestoreBindingOrValue
            }
            enabled: checkbox.isAvailable
            onToggled: checkbox.componentToggled(box.checked, checkbox.componentId)
            Accessible.name: checkbox.componentName
            Layout.alignment: Qt.AlignVCenter
            palette.windowText: ThemeColors.fgColor(checkbox.glassMode)
            palette.text: ThemeColors.fgColor(checkbox.glassMode)
        }

        // Icon
        Kirigami.Icon {
            source: checkbox.componentIcon
            Layout.preferredWidth: Platform.Units.iconSizes.medium
            Layout.preferredHeight: Platform.Units.iconSizes.medium
            color: checkbox.isAvailable ? ThemeColors.fgColor(checkbox.glassMode) : ThemeColors.disabledColor(checkbox.glassMode)
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
                    color: checkbox.isAvailable ? ThemeColors.fgColor(checkbox.glassMode) : ThemeColors.disabledColor(checkbox.glassMode)
                }

                Label {
                    text: checkbox.statusLabel
                    font.pointSize: TypeScale.caption
                    color: checkbox.statusColor
                    visible: !checkbox.isAvailable || checkbox.componentStatus === "partial"
                }

                Label {
                    text: qsTr("Live")
                    font.pointSize: TypeScale.caption
                    color: ThemeColors.accent()
                    visible: checkbox.componentSupportsLiveReload && checkbox.isAvailable
                }
            }

            Label {
                text: checkbox.componentDescription
                font.pointSize: TypeScale.caption
                color: ThemeColors.dimColor(checkbox.glassMode)
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                visible: checkbox.componentDescription !== ""
            }
        }
    }

    background: Rectangle {
        radius: 4
        color: ThemeColors.nestedBg(checkbox.glassMode)
    }
}
