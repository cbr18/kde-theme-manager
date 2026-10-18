import QtQuick
import org.kde.kirigami.platform as Platform
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami

Kirigami.Page {
    id: page
    title: qsTr("Settings")
    scrollable: true

    ColumnLayout {
        Layout.fillWidth: true
        spacing: Platform.Units.largeSpacing
        Layout.leftMargin: Platform.Units.largeSpacing
        Layout.rightMargin: Platform.Units.largeSpacing
        Layout.topMargin: Platform.Units.largeSpacing
        Layout.bottomMargin: Platform.Units.largeSpacing

        // ─── Profile Apply Mode ───
        Kirigami.Card {
            Layout.fillWidth: true

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Platform.Units.mediumSpacing

                Kirigami.Heading {
                    level: 2
                    text: qsTr("Profile Apply Mode")
                }

                Kirigami.FormLayout {
                    Layout.fillWidth: true

                    Kirigami.FormData.label: qsTr("Mode")
                    Kirigami.FormData.isRequired: true

                    RowLayout {
                        spacing: Platform.Units.mediumSpacing

                        Kirigami.RadioButton {
                            id: modeAll
                            text: qsTr("Apply ALL components (default)")
                            checked: settingsController.defaultComponentsMode === "all"
                            onToggled: if (checked) settingsController.defaultComponentsMode = "all"
                            hoverEnabled: true
                            ToolTip.text: qsTr("Apply all tracked components when switching profiles")
                            ToolTip.visible: hovered
                        }

                        Kirigami.RadioButton {
                            id: modeCustom
                            text: qsTr("Apply SELECTED components only")
                            checked: settingsController.defaultComponentsMode === "custom"
                            onToggled: if (checked) settingsController.defaultComponentsMode = "custom"
                            hoverEnabled: true
                            ToolTip.text: qsTr("Choose which components to apply per profile")
                            ToolTip.visible: hovered
                        }
                    }
                }

                // Custom components selection (visible when custom mode)
                Item {
                    Layout.fillWidth: true
                    visible: settingsController.defaultComponentsMode === "custom"
                    height: customComponentsView.height

                    Kirigami.Separator {}

                    Label {
                        text: qsTr("Select components to include when applying/saving profiles:")
                        font.pointSize: Platform.Units.smallSpacing
                        color: Kirigami.Theme.textColor
                        opacity: 0.7
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    // Component checkboxes grouped by category
                    ColumnLayout {
                        id: customComponentsView
                        Layout.fillWidth: true
                        spacing: Platform.Units.mediumSpacing

                        Repeater {
                            id: categoryRepeater
                            model: trackedAppsController.categories
                            delegate: ComponentCategoryGroup {
                                category: modelData
                                selectedComponents: settingsController.customComponents
                                availableComponents: settingsController.availableComponents
                                onSelectionChanged: {
                                    // selectedComponents on this group was updated to the local
                                    // _localSelection (which mirrors the full selection set),
                                    // so propagate it back to the SettingsController.
                                    settingsController.customComponents = selectedComponents.slice()
                                }
                            }
                        }
                    }
                }
            }
        }

        // ─── Wallpaper Settings ───
        Kirigami.Card {
            Layout.fillWidth: true

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Platform.Units.mediumSpacing

                Kirigami.Heading {
                    level: 2
                    text: qsTr("Wallpaper")
                }

                Kirigami.FormLayout {
                    Layout.fillWidth: true

                    Kirigami.FormData.label: qsTr("Link wallpaper to profile")
                    Kirigami.FormData.isRequired: false

                    Kirigami.Switch {
                        checked: settingsController.wallpaperLinkedToProfile
                        onToggled: settingsController.wallpaperLinkedToProfile = checked
                    }

                    Kirigami.FormData.label: qsTr("Wallpaper directory")
                    Kirigami.FormData.isRequired: true

                    RowLayout {
                        TextField {
                            Layout.fillWidth: true
                            text: settingsController.wallpaperDirectory
                            placeholderText: "~/Изображения/Wallpaper"
                            onEditingFinished: settingsController.wallpaperDirectory = text
                        }
                        Kirigami.Button {
                            icon.name: "folder-open"
                            flat: true
                            onClicked: {
                                // TODO: open folder dialog
                            }
                        }
                    }
                }
            }
        }

        // ─── UI Settings ───
        Kirigami.Card {
            Layout.fillWidth: true

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Platform.Units.mediumSpacing

                Kirigami.Heading {
                    level: 2
                    text: qsTr("Appearance")
                }

                Kirigami.FormLayout {
                    Layout.fillWidth: true

                    Kirigami.FormData.label: qsTr("Application theme")

                    ComboBox {
                        Layout.fillWidth: true
                        model: ["system", "glass", "paper", "dark", "light"]
                        currentText: settingsController.theme
                        onCurrentTextChanged: settingsController.theme = currentText
                    }
                }
            }
        }

        // ─── Behavior Settings ───
        Kirigami.Card {
            Layout.fillWidth: true

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Platform.Units.mediumSpacing

                Kirigami.Heading {
                    level: 2
                    text: qsTr("Behavior")
                }

                Kirigami.FormLayout {
                    Layout.fillWidth: true

                    Kirigami.FormData.label: qsTr("Show warning for not installed apps")
                    Kirigami.Switch {
                        checked: settingsController.showNotInstalledWarning
                        onToggled: settingsController.showNotInstalledWarning = checked
                    }

                    Kirigami.FormData.label: qsTr("Auto-apply last profile on startup")
                    Kirigami.Switch {
                        checked: settingsController.autoApplyOnStartup
                        onToggled: settingsController.autoApplyOnStartup = checked
                    }

                    Kirigami.FormData.label: qsTr("Minimize to system tray")
                    Kirigami.Switch {
                        checked: settingsController.minimizeToTray
                        onToggled: settingsController.minimizeToTray = checked
                    }

                    Kirigami.FormData.label: qsTr("Confirm before applying profile")
                    Kirigami.Switch {
                        checked: settingsController.confirmBeforeApply
                        onToggled: settingsController.confirmBeforeApply = checked
                    }

                    Kirigami.FormData.label: qsTr("Create backup before applying")
                    Kirigami.Switch {
                        checked: settingsController.createBackupBeforeApply
                        onToggled: settingsController.createBackupBeforeApply = checked
                    }

                    Kirigami.FormData.label: qsTr("Global hotkey")
                    RowLayout {
                        TextField {
                            Layout.fillWidth: true
                            text: settingsController.globalHotkey
                            placeholderText: "Meta+T"
                            onEditingFinished: settingsController.globalHotkey = text
                        }
                    }
                }
            }
        }

        // ─── Actions ───
        Kirigami.Card {
            Layout.fillWidth: true

            RowLayout {
                spacing: Platform.Units.mediumSpacing

                Kirigami.Button {
                    Layout.fillWidth: true
                    text: qsTr("Save Settings")
                    icon.name: "document-save"
                    highlighted: true
                    onClicked: settingsController.save()
                }

                Kirigami.Button {
                    Layout.fillWidth: true
                    text: qsTr("Reset to Defaults")
                    icon.name: "view-refresh"
                    onClicked: settingsController.resetToDefaults()
                }
            }
        }
    }
}