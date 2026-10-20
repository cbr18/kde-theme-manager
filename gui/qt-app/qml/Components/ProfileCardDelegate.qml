import QtQuick
import org.kde.kirigami.platform as Platform
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami

Kirigami.AbstractCard {
    id: card

    Layout.fillWidth: true

    // Explicit data (avoids relying on QML model-role semantics)
    property string profileName: ""
    property bool profileIsActive: false
    property int profileComponentCount: 0
    property var profileComponents: []
    // Glass mode is passed down because QML components cannot see the
    // root window's properties across component-file scopes.
    property bool glassMode: false

    property var compList: profileComponents ? profileComponents : []
    property var firstComponents: compList.slice(0, 8)
    property bool hasMore: compList.length > 8

    function getComponentIcon(compId) {
        const icons = {
            "kwin": "preferences-system-windows",
            "plasma_shell": "plasma",
            "kdeglobals": "preferences-desktop-theme",
            "gtk3": "gtk-preferences",
            "gtk4": "gtk-preferences",
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
            "obsidian": "x-office-document",
            "color_schemes": "preferences-desktop-color",
            "look_and_feel": "preferences-desktop-theme"
        }
        return icons[compId] || "application-x-executable"
    }

    contentItem: ColumnLayout {
        spacing: Platform.Units.smallSpacing

        // ─── Header ───
        RowLayout {
            Layout.fillWidth: true
            spacing: Platform.Units.mediumSpacing

            Kirigami.Icon {
                source: "preferences-desktop-theme"
                Layout.preferredWidth: Platform.Units.iconSizes.large
                Layout.preferredHeight: Platform.Units.iconSizes.large
                color: ThemeColors.accent()
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Label {
                    text: card.profileName === "glass" ? qsTr("Glass")
                        : card.profileName === "paper" ? qsTr("Paper")
                        : card.profileName
                    font.bold: true
                    font.pointSize: TypeScale.subtitle
                    color: ThemeColors.fgColor(card.glassMode)
                }

                Label {
                    text: qsTr("%1 components").arg(card.profileComponentCount)
                    font.pointSize: TypeScale.caption
                    color: ThemeColors.dimColor(card.glassMode)
                }
            }

            Item { Layout.fillWidth: true }

            // Active badge
            Kirigami.Icon {
                source: "dialog-ok-apply"
                visible: card.profileIsActive
                color: ThemeColors.positive()
                Layout.preferredWidth: Platform.Units.iconSizes.medium
                Layout.preferredHeight: Platform.Units.iconSizes.medium
            }
        }

        // ─── Component tags ───
        Flow {
            Layout.fillWidth: true
            spacing: 4
            visible: card.firstComponents.length > 0

            Repeater {
                model: card.firstComponents
                delegate: Kirigami.Chip {
                    text: modelData
                    icon.name: card.getComponentIcon(modelData)
                    closable: false
                }
            }

            Loader {
                active: card.hasMore
                sourceComponent: moreChip
            }
        }

        // ─── Actions ───
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }

            Button {
                icon.name: card.profileIsActive ? "view-refresh" : "dialog-ok-apply"
                flat: true
                ToolTip.text: card.profileIsActive ? qsTr("Re-apply profile") : qsTr("Apply profile")
                ToolTip.visible: hovered
                Accessible.name: ToolTip.text
                Accessible.role: Accessible.Button
                onClicked: card.applyClicked(card.profileName)
            }

            Button {
                icon.name: "document-preview"
                flat: true
                visible: !card.profileIsActive
                ToolTip.text: qsTr("Preview changes before applying")
                ToolTip.visible: hovered
                Accessible.name: ToolTip.text
                Accessible.role: Accessible.Button
                onClicked: card.previewClicked(card.profileName)
            }

            Button {
                icon.name: "document-properties"
                flat: true
                visible: !card.profileIsActive
                ToolTip.text: qsTr("Compare with active profile")
                ToolTip.visible: hovered
                Accessible.name: ToolTip.text
                Accessible.role: Accessible.Button
                onClicked: card.diffClicked(card.profileName)
            }

            Button {
                icon.name: "preferences-desktop-theme"
                flat: true
                ToolTip.text: qsTr("Inspect the theme values stored in this profile")
                ToolTip.visible: hovered
                Accessible.name: ToolTip.text
                Accessible.role: Accessible.Button
                onClicked: card.inspectClicked(card.profileName)
            }

            Button {
                icon.name: "edit-delete"
                flat: true
                visible: !card.profileIsActive
                ToolTip.text: qsTr("Delete profile")
                ToolTip.visible: hovered
                Accessible.name: ToolTip.text
                Accessible.role: Accessible.Button
                onClicked: card.deleteClicked(card.profileName)
            }
        }
    }

    Component {
        id: moreChip
        Kirigami.Chip {
            text: "+" + Math.max(0, card.compList.length - 8)
            icon.name: "view-more"
            ToolTip.text: qsTr("%1 more components").arg(Math.max(0, card.compList.length - 8))
            ToolTip.visible: hovered
        }
    }

    background: Rectangle {
        radius: 8
        border.width: 1
        color: ThemeColors.cardBg(card.glassMode)
        border.color: ThemeColors.cardBorder(card.glassMode)
    }

    // Signals
    signal applyClicked(string profileName)
    signal previewClicked(string profileName)
    signal diffClicked(string profileName)
    signal inspectClicked(string profileName)
    signal deleteClicked(string profileName)
}
