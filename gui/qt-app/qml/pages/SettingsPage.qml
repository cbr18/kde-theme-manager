import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami
import org.kde.kirigami.platform as Platform
import Components 1.0

Kirigami.ScrollablePage {
    id: page

    title: qsTr("Settings")

    readonly property bool glassMode: themeController.isGlass

    background: Rectangle {
        color: page.glassMode ? ThemeColors.glassPanel() : ThemeColors.pageBg(page.glassMode)
    }

    // Single top-level layout: ScrollablePage only anchors its child
    // left/right, so everything must live inside a layout.
    ColumnLayout {
        Layout.margins: Platform.Units.largeSpacing
        spacing: Platform.Units.largeSpacing

        // ─── Profile Apply Mode ───
        Kirigami.Card {
            Layout.fillWidth: true

            background: Rectangle {
                radius: Platform.Units.smallSpacing
                border.width: 1
                color: ThemeColors.cardBg(page.glassMode)
                border.color: ThemeColors.cardBorder(page.glassMode)
            }

            contentItem: ColumnLayout {
                spacing: Platform.Units.mediumSpacing

                Kirigami.Heading {
                    level: 2
                    text: qsTr("Profile Apply Mode")
                    color: ThemeColors.fgColor(page.glassMode)
                }

                Kirigami.FormLayout {
                    Layout.fillWidth: true

                    RowLayout {
                        Kirigami.FormData.label: qsTr("Mode")
                        spacing: Platform.Units.mediumSpacing

                        RadioButton {
                            id: modeAll
                            text: qsTr("Apply ALL components (default)")
                            autoExclusive: true
                            hoverEnabled: true
                            ToolTip.text: qsTr("Apply all tracked components when switching profiles")
                            ToolTip.visible: hovered
                            onClicked: if (checked) settingsController.defaultComponentsMode = "all"
                            Binding {
                                target: modeAll
                                property: "checked"
                                value: settingsController.defaultComponentsMode === "all"
                                restoreMode: Binding.RestoreBindingOrValue
                            }
                        }

                        RadioButton {
                            id: modeCustom
                            text: qsTr("Apply SELECTED components only")
                            autoExclusive: true
                            hoverEnabled: true
                            ToolTip.text: qsTr("Choose which components to apply per profile")
                            ToolTip.visible: hovered
                            onClicked: if (checked) settingsController.defaultComponentsMode = "custom"
                            Binding {
                                target: modeCustom
                                property: "checked"
                                value: settingsController.defaultComponentsMode === "custom"
                                restoreMode: Binding.RestoreBindingOrValue
                            }
                        }
                    }
                }

                // Custom components selection (visible when custom mode)
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Platform.Units.mediumSpacing
                    visible: settingsController.defaultComponentsMode === "custom"

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: ThemeColors.subtleBorder(page.glassMode)
                    }

                    Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: qsTr("Select components to include when applying/saving profiles:")
                        font.pointSize: TypeScale.caption
                        color: ThemeColors.dimColor(page.glassMode)
                    }

                    // Component checkboxes grouped by category
                    Repeater {
                        model: trackedAppsController.categories
                        delegate: ComponentCategoryGroup {
                            category: modelData
                            selectedComponents: settingsController.customComponents
                            availableComponents: settingsController.availableComponents
                            glassMode: page.glassMode
                            onSelectionChanged: (components) => settingsController.customComponents = components
                        }
                    }
                }
            }
        }

        // ─── Wallpaper Settings ───
        Kirigami.Card {
            Layout.fillWidth: true

            background: Rectangle {
                radius: Platform.Units.smallSpacing
                border.width: 1
                color: ThemeColors.cardBg(page.glassMode)
                border.color: ThemeColors.cardBorder(page.glassMode)
            }

            contentItem: ColumnLayout {
                spacing: Platform.Units.mediumSpacing

                Kirigami.Heading {
                    level: 2
                    text: qsTr("Wallpaper")
                    color: ThemeColors.fgColor(page.glassMode)
                }

                Kirigami.FormLayout {
                    Layout.fillWidth: true

                    Switch {
                        id: wallpaperLinkedSwitch
                        text: qsTr("Link wallpaper to profile")
                        onToggled: settingsController.wallpaperLinkedToProfile = checked
                        Binding {
                            target: wallpaperLinkedSwitch
                            property: "checked"
                            value: settingsController.wallpaperLinkedToProfile
                            restoreMode: Binding.RestoreBindingOrValue
                        }
                    }

                    RowLayout {
                        Kirigami.FormData.label: qsTr("Wallpaper directory")

                        TextField {
                            Layout.fillWidth: true
                            text: settingsController.wallpaperDirectory
                            placeholderText: "~/Изображения/Wallpaper"
                            onEditingFinished: settingsController.wallpaperDirectory = text
                        }
                        Button {
                            icon.name: "folder-open"
                            flat: true
                            enabled: false
                            hoverEnabled: true
                            Accessible.name: qsTr("Choose wallpaper directory")
                            ToolTip.text: qsTr("Not implemented yet")
                            ToolTip.visible: hovered
                        }
                    }
                }
            }
        }

        // ─── UI Settings ───
        Kirigami.Card {
            Layout.fillWidth: true

            background: Rectangle {
                radius: Platform.Units.smallSpacing
                border.width: 1
                color: ThemeColors.cardBg(page.glassMode)
                border.color: ThemeColors.cardBorder(page.glassMode)
            }

            contentItem: ColumnLayout {
                spacing: Platform.Units.mediumSpacing

                Kirigami.Heading {
                    level: 2
                    text: qsTr("Appearance")
                    color: ThemeColors.fgColor(page.glassMode)
                }

                Kirigami.FormLayout {
                    Layout.fillWidth: true

                    ComboBox {
                        id: themeCombo
                        Layout.fillWidth: true
                        Kirigami.FormData.label: qsTr("Application theme")
                        model: ["system", "glass", "paper", "dark", "light"]
                        onActivated: settingsController.theme = currentText
                        Binding {
                            target: themeCombo
                            property: "currentIndex"
                            value: themeCombo.model.indexOf(settingsController.theme)
                            restoreMode: Binding.RestoreBindingOrValue
                        }
                    }
                }
            }
        }

        // ─── Behavior Settings ───
        Kirigami.Card {
            Layout.fillWidth: true

            background: Rectangle {
                radius: Platform.Units.smallSpacing
                border.width: 1
                color: ThemeColors.cardBg(page.glassMode)
                border.color: ThemeColors.cardBorder(page.glassMode)
            }

            contentItem: ColumnLayout {
                spacing: Platform.Units.mediumSpacing

                Kirigami.Heading {
                    level: 2
                    text: qsTr("Behavior")
                    color: ThemeColors.fgColor(page.glassMode)
                }

                Kirigami.FormLayout {
                    Layout.fillWidth: true

                    Switch {
                        id: notInstalledSwitch
                        Kirigami.FormData.label: qsTr("Show warning for not installed apps")
                        onToggled: settingsController.showNotInstalledWarning = checked
                        Binding {
                            target: notInstalledSwitch
                            property: "checked"
                            value: settingsController.showNotInstalledWarning
                            restoreMode: Binding.RestoreBindingOrValue
                        }
                    }

                    Switch {
                        id: autoApplySwitch
                        Kirigami.FormData.label: qsTr("Auto-apply last profile on startup")
                        onToggled: settingsController.autoApplyOnStartup = checked
                        Binding {
                            target: autoApplySwitch
                            property: "checked"
                            value: settingsController.autoApplyOnStartup
                            restoreMode: Binding.RestoreBindingOrValue
                        }
                    }

                    Switch {
                        id: minimizeSwitch
                        Kirigami.FormData.label: qsTr("Minimize to system tray")
                        onToggled: settingsController.minimizeToTray = checked
                        Binding {
                            target: minimizeSwitch
                            property: "checked"
                            value: settingsController.minimizeToTray
                            restoreMode: Binding.RestoreBindingOrValue
                        }
                    }

                    Switch {
                        id: confirmSwitch
                        Kirigami.FormData.label: qsTr("Confirm before applying profile")
                        onToggled: settingsController.confirmBeforeApply = checked
                        Binding {
                            target: confirmSwitch
                            property: "checked"
                            value: settingsController.confirmBeforeApply
                            restoreMode: Binding.RestoreBindingOrValue
                        }
                    }

                    Switch {
                        id: backupSwitch
                        Kirigami.FormData.label: qsTr("Create backup before applying")
                        onToggled: settingsController.createBackupBeforeApply = checked
                        Binding {
                            target: backupSwitch
                            property: "checked"
                            value: settingsController.createBackupBeforeApply
                            restoreMode: Binding.RestoreBindingOrValue
                        }
                    }

                    TextField {
                        Kirigami.FormData.label: qsTr("Global hotkey")
                        Layout.fillWidth: true
                        text: settingsController.globalHotkey
                        placeholderText: "Meta+T"
                        onEditingFinished: settingsController.globalHotkey = text
                    }
                }
            }
        }

        // ─── Actions ───
        Kirigami.Card {
            Layout.fillWidth: true

            background: Rectangle {
                radius: Platform.Units.smallSpacing
                border.width: 1
                color: ThemeColors.cardBg(page.glassMode)
                border.color: ThemeColors.cardBorder(page.glassMode)
            }

            contentItem: RowLayout {
                spacing: Platform.Units.mediumSpacing

                Button {
                    Layout.fillWidth: true
                    text: qsTr("Save Settings")
                    icon.name: "document-save"
                    highlighted: true
                    onClicked: settingsController.save()
                }

                Button {
                    Layout.fillWidth: true
                    text: qsTr("Reset to Defaults")
                    icon.name: "view-refresh"
                    onClicked: settingsController.resetToDefaults()
                }
            }
        }
    }
}
