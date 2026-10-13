import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami

Kirigami.AbstractCard {
    id: card
    Layout.fillWidth: true
    contentItem: ColumnLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing

        // Header
        RowLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.mediumSpacing

            Kirigami.Icon {
                source: "preferences-desktop-theme"
                Layout.preferredWidth: Kirigami.Units.iconSizes.large
                Layout.preferredHeight: Kirigami.Units.iconSizes.large
                color: Kirigami.Theme.highlightColor
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Label {
                    text: model.name === "glass" ? i18n("Glass") :
                          model.name === "paper" ? i18n("Paper") : model.name
                    font.bold: true
                    font.pointSize: Kirigami.Units.fontSizes.medium
                }

                Label {
                    text: i18n("%1 components", model.componentCount)
                    font.pointSize: Kirigami.Units.fontSizes.small
                    color: Kirigami.Theme.textColor
                    opacity: 0.7
                }
            }

            // Active badge
            Item { Layout.fillWidth: true }

            Kirigami.Icon {
                source: "dialog-ok-apply"
                visible: model.isActive
                color: Kirigami.Theme.positiveTextColor
                Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                tooltip: i18n("Active profile")
            }
        }

        // Component tags
        Flow {
            Layout.fillWidth: true
            spacing: 4
            Repeater {
                model: model.components.slice(0, 8)
                delegate: Kirigami.Chip {
                    text: modelData
                    icon.source: getComponentIcon(modelData)
                    closable: false
                }
            }
            Loader {
                // +N more
                sourceComponent: model.components.length > 8 ? moreChip : null
            }
        }

        Component {
            id: moreChip
            Kirigami.Chip {
                text: "+" + (model.components.length - 8)
                icon.source: "view-more"
            }
        }

        // Actions
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }

            Kirigami.IconButton {
                icon.source: model.isActive ? "view-refresh" : "dialog-ok-apply"
                tooltip: model.isActive ? i18n("Reapply") : i18n("Apply")
                onClicked: applyClicked(model.name)
            }

            Kirigami.IconButton {
                icon.source: "document-properties"
                tooltip: i18n("Diff with active")
                visible: !model.isActive
                onClicked: diffClicked(model.name)
            }

            Kirigami.IconButton {
                icon.source: "edit-delete"
                tooltip: i18n("Delete")
                visible: !model.isActive
                onClicked: deleteClicked(model.name)
            }
        }
    }

    // Signals
    signal applyClicked(string profileName)
    signal diffClicked(string profileName)
    signal deleteClicked(string profileName)

    function getComponentIcon(compId: string): string {
        const icons: Record<string, string> = {
            "kwin": "preferences-system-windows",
            "plasma_shell": "plasma",
            "kdeglobals": "preferences-desktop-theme",
            "gtk3": "preferences-desktop-theme-gtk",
            "gtk4": "preferences-desktop-theme-gtk",
            "qt5ct": "qtlogo",
            "klassy": "preferences-system-windows",
            "kvantum": "preferences-system-windows",
            "kitty": "utilities-terminal",
            "alacritty": "utilities-terminal",
            "wofi": "system-run",
            "btop": "utilities-system-monitor",
            "fastfetch": "preferences-desktop-theme",
            "zed": "text-editor",
            "vscode": "visual-studio-code",
            "cursor": "text-editor",
            "zen": "web-browser",
            "obsidian": "x-office-note",
            "color_schemes": "preferences-desktop-color",
            "look_and_feel": "preferences-desktop-theme",
        }
        return icons[compId] || "application-x-executable"
    }
}