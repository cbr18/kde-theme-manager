import QtQuick
import org.kde.kirigami.platform as Platform
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami

Kirigami.AbstractCard {
    id: card
    Layout.fillWidth: true

    // Extract components array for use in Flow
    property var compList: (model.components || [])
    property var firstComponents: compList.slice(0, 8)
    property var hasMore: compList.length > 8

    contentItem: ColumnLayout {
        Layout.fillWidth: true
        spacing: Platform.Units.smallSpacing

        // Header
        RowLayout {
            Layout.fillWidth: true
            spacing: Platform.Units.mediumSpacing

            Kirigami.Icon {
                source: "preferences-desktop-theme"
                Layout.preferredWidth: Platform.Units.iconSizes.large
                Layout.preferredHeight: Platform.Units.iconSizes.large
                color: Kirigami.Theme.highlightColor
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Label {
                    text: model.name === "glass" ? qsTr("Glass") :
                          model.name === "paper" ? qsTr("Paper") : model.name
                    font.bold: true
                    font.pointSize: Platform.Units.mediumSpacing
                }

                Label {
                    text: qsTr("%1 components").arg(model.componentCount)
                    font.pointSize: Platform.Units.smallSpacing
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
                Layout.preferredWidth: Platform.Units.iconSizes.medium
                Layout.preferredHeight: Platform.Units.iconSizes.medium
            }
        }

        // Component tags
        Flow {
            Layout.fillWidth: true
            spacing: 4
            Repeater {
                model: firstComponents
                delegate: Kirigami.Chip {
                    text: modelData
                    icon.name: getComponentIcon(modelData)
                    closable: false
                }
            }
            Loader {
                // +N more
                sourceComponent: hasMore ? moreChip : null
            }
        }

        Component {
            id: moreChip
            Kirigami.Chip {
                text: "+" + (card.compList.length - 8)
                icon.name: "view-more"
            }
        }

        // Actions
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }

            Button {
                icon.name: model.isActive ? "view-refresh" : "dialog-ok-apply"
                flat: true
                onClicked: applyClicked(model.name)
            }

            Button {
                icon.name: "document-preview"
                flat: true
                visible: !model.isActive
                onClicked: previewClicked(model.name)
            }

            Button {
                icon.name: "document-properties"
                flat: true
                visible: !model.isActive
                onClicked: diffClicked(model.name)
            }

            Button {
                icon.name: "edit-delete"
                flat: true
                visible: !model.isActive
                onClicked: deleteClicked(model.name)
            }
        }
    }

    // Signals
    signal applyClicked(string profileName)
    signal previewClicked(string profileName)
    signal diffClicked(string profileName)
    signal deleteClicked(string profileName)

    function getComponentIcon(compId) {
        const icons = {
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