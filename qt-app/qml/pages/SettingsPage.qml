import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami

Kirigami.Page {
    id: page
    title: i18n("Settings")
    scrollable: true

    ColumnLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.largeSpacing
        Layout.leftMargin: Kirigami.Units.largeSpacing
        Layout.rightMargin: Kirigami.Units.largeSpacing
        Layout.topMargin: Kirigami.Units.largeSpacing
        Layout.bottomMargin: Kirigami.Units.largeSpacing

        // ─── Profile Apply Mode ───
        Kirigami.Card {
            Layout.fillWidth: true

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.mediumSpacing

                RowLayout {
                    Kirigami.Heading {
                        level: 2
                        text: i18n("Profile Apply Mode")
                    }
                }

                Kirigami.FormLayout {
                    Layout.fillWidth: true

                    // Mode selector
                    Kirigami.FormData.label: i18n("Mode")
                    Kirigami.FormData.isRequired: true

                    RowLayout {
                        spacing: Kirigami.Units.mediumSpacing

                        Kirigami.RadioButton {
                            id: modeAll
                            text: i18n("Apply ALL components (default)")
                            checked: mainController.settings.defaultComponentsMode === "all"
                            onToggled: if (checked) mainController.settings.defaultComponentsMode = "all"
                            tooltip: i18n("Apply all tracked components when switching profiles")
                        }

                        Kirigami.RadioButton {
                            id: modeCustom
                            text: i18n("Apply SELECTED components only")
                            checked: mainController.settings.defaultComponentsMode === "custom"
                            onToggled: if (checked) mainController.settings.defaultComponentsMode = "custom"
                            tooltip: i18n("Choose which components to apply per profile")
                        }
                    }
                }

                // Custom components selection (visible when custom mode)
                Item {
                    Layout.fillWidth: true
                    visible: mainController.settings.defaultComponentsMode === "custom"
                    height: customComponentsView.height

                    Kirigami.Separator {}

                    Label {
                        text: i18n("Select components to include when applying/saving profiles:")
                        font.pointSize: Kirigami.Units.fontSizes.small
                        color: Kirigami.Theme.textColor
                        opacity: 0.7
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    // Component checkboxes grouped by category
                    ColumnLayout {
                        id: customComponentsView
                        Layout.fillWidth: true
                        spacing: Kirigami.Units.mediumSpacing

                        Repeater {
                            model: mainController.tracked_apps.categories
                            delegate: ComponentCategoryGroup {
                                category: modelData
                                selectedComponents: mainController.settings.customComponents
                                availableComponents: mainController.settings.availableComponents
                                onSelectionChanged: {
                                    // Обновить список выбранных компонентов
                                    var selected = []
                                    for (var cat in mainController.tracked_apps.categories) {
                                        var comps = mainController.tracked_apps.getComponentsByCategory(cat)
                                        for (var i = 0; i < comps.length; i++) {
                                            if (comps[i].selected) {
                                                selected.push(comps[i].id)
                                            }
                                        }
                                    }
                                    mainController.settings.customComponents = selected
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
                spacing: Kirigami.Units.mediumSpacing

                Kirigami.Heading {
                    level: 2
                    text: i18n("Wallpaper")
                }

                Kirigami.FormLayout {
                    Layout.fillWidth: true

                    Kirigami.FormData.label: i18n("Link wallpaper to profile")
                    Kirigami.FormData.isRequired: false

                    Kirigami.Switch {
                        checked: mainController.settings.wallpaperLinkedToProfile
                        onToggled: mainController.settings.wallpaperLinkedToProfile = checked
                    }

                    Kirigami.FormData.label: i18n("Wallpaper directory")
                    Kirigami.FormData.isRequired: true

                    RowLayout {
                        TextField {
                            Layout.fillWidth: true
                            text: mainController.settings.wallpaperDirectory
                            placeholderText: "~/Изображения/Wallpaper"
                            onEditingFinished: mainController.settings.wallpaperDirectory = text
                        }
                        Kirigami.IconButton {
                            icon.source: "folder-open"
                            onClicked: {
                                // TODO: открыть диалог выбора папки
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
                spacing: Kirigami.Units.mediumSpacing

                Kirigami.Heading {
                    level: 2
                    text: i18n("Appearance")
                }

                Kirigami.FormLayout {
                    Layout.fillWidth: true

                    Kirigami.FormData.label: i18n("Application theme")

                    ComboBox {
                        Layout.fillWidth: true
                        model: ["system", "glass", "paper", "dark", "light"]
                        currentText: mainController.settings.theme
                        onCurrentTextChanged: mainController.settings.theme = currentText
                    }
                }
            }
        }

        // ─── Behavior Settings ───
        Kirigami.Card {
            Layout.fillWidth: true

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.mediumSpacing

                Kirigami.Heading {
                    level: 2
                    text: i18n("Behavior")
                }

                Kirigami.FormLayout {
                    Layout.fillWidth: true

                    Kirigami.FormData.label: i18n("Show warning for not installed apps")
                    Kirigami.Switch {
                        checked: mainController.settings.showNotInstalledWarning
                        onToggled: mainController.settings.showNotInstalledWarning = checked
                    }

                    Kirigami.FormData.label: i18n("Auto-apply last profile on startup")
                    Kirigami.Switch {
                        checked: mainController.settings.autoApplyOnStartup
                        onToggled: mainController.settings.autoApplyOnStartup = checked
                    }

                    Kirigami.FormData.label: i18n("Minimize to system tray")
                    Kirigami.Switch {
                        checked: mainController.settings.minimizeToTray
                        onToggled: mainController.settings.minimizeToTray = checked
                    }

                    Kirigami.FormData.label: i18n("Confirm before applying profile")
                    Kirigami.Switch {
                        checked: mainController.settings.confirmBeforeApply
                        onToggled: mainController.settings.confirmBeforeApply = checked
                    }

                    Kirigami.FormData.label: i18n("Create backup before applying")
                    Kirigami.Switch {
                        checked: mainController.settings.createBackupBeforeApply
                        onToggled: mainController.settings.createBackupBeforeApply = checked
                    }

                    Kirigami.FormData.label: i18n("Global hotkey")
                    RowLayout {
                        TextField {
                            Layout.fillWidth: true
                            text: mainController.settings.globalHotkey
                            placeholderText: "Meta+T"
                            onEditingFinished: mainController.settings.globalHotkey = text
                        }
                    }
                }
            }
        }

        // ─── Actions ───
        Kirigami.Card {
            Layout.fillWidth: true

            RowLayout {
                spacing: Kirigami.Units.mediumSpacing

                Kirigami.Button {
                    Layout.fillWidth: true
                    text: i18n("Save Settings")
                    icon.source: "document-save"
                    highlighted: true
                    onClicked: mainController.settings.save()
                }

                Kirigami.Button {
                    Layout.fillWidth: true
                    text: i18n("Reset to Defaults")
                    icon.source: "view-refresh"
                    onClicked: mainController.settings.resetToDefaults()
                }
            }
        }
    }
}