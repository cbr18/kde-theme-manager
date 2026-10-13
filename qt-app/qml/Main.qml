import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami
import org.kde.kirigami.addons 1.0 as KirigamiAddons

Kirigami.ApplicationWindow {
    id: root
    title: i18n("Theme Profile Manager")
    width: 720
    height: 560
    minimumWidth: 600
    minimumHeight: 480

    // Глобальные настройки
    property bool isDarkTheme: Kirigami.Theme.highlightColor.r < 0.5

    // ──────────────────────────────────────────────────────────────
    // Главная страница (профили + обои)
    // ──────────────────────────────────────────────────────────────

    pageStack.initialPage: Kirigami.Page {
        id: mainPage
        title: i18n("Theme Profiles")

        Kirigami.ScrollablePage {
            columnLayout: true

            // ─── Header: Active Profile ───
            Kirigami.Card {
                Layout.fillWidth: true
                Layout.leftMargin: Kirigami.Units.largeSpacing
                Layout.rightMargin: Kirigami.Units.largeSpacing
                Layout.topMargin: Kirigami.Units.largeSpacing

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing

                    RowLayout {
                        Layout.fillWidth: true
                        Kirigami.Heading {
                            level: 2
                            text: i18n("Active Profile")
                        }
                        Item { Layout.fillWidth: true }
                        Kirigami.IconButton {
                            icon.source: "view-refresh"
                            onClicked: mainController.profile.refresh()
                            tooltip: i18n("Refresh profiles")
                        }
                    }

                    RowLayout {
                        spacing: Kirigami.Units.mediumSpacing
                        Repeater {
                            model: mainController.profile.profiles
                            delegate: ProfileRadioButton {
                                profileName: model.name
                                isActive: model.isActive
                                componentCount: model.componentCount
                                onClicked: {
                                    if (!model.isActive) {
                                        mainController.profile.applyProfile(model.name)
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ─── Profiles Grid ───
            Kirigami.Card {
                Layout.fillWidth: true
                Layout.leftMargin: Kirigami.Units.largeSpacing
                Layout.rightMargin: Kirigami.Units.largeSpacing
                Layout.topMargin: Kirigami.Units.mediumSpacing

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing

                    RowLayout {
                        Kirigami.Heading {
                            level: 3
                            text: i18n("Available Profiles")
                        }
                        Item { Layout.fillWidth: true }
                        Kirigami.IconButton {
                            icon.source: "list-add"
                            onClicked: showSaveDialog()
                            tooltip: i18n("Save current as new profile")
                        }
                    }

                    Kirigami.CardsListView {
                        Layout.fillWidth: true
                        Layout.minimumHeight: 180
                        model: mainController.profile.profiles
                        delegate: ProfileCardDelegate {
                            onApplyClicked: mainController.profile.applyProfile(model.name)
                            onDeleteClicked: {
                                if (mainController.settings.confirmBeforeApply) {
                                    confirmDialog.text = i18n("Delete profile \"%1\"?", model.name)
                                    confirmDialog.open()
                                } else {
                                    mainController.profile.deleteProfile(model.name)
                                }
                            }
                            onDiffClicked: {
                                diffDialog.profileA = model.name
                                diffDialog.profileB = mainController.profile.activeProfile
                                diffDialog.open()
                            }
                        }
                    }
                }
            }

            // ─── Wallpaper Section ───
            Kirigami.Card {
                Layout.fillWidth: true
                Layout.leftMargin: Kirigami.Units.largeSpacing
                Layout.rightMargin: Kirigami.Units.largeSpacing
                Layout.topMargin: Kirigami.Units.mediumSpacing
                Layout.bottomMargin: Kirigami.Units.largeSpacing

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing

                    RowLayout {
                        Kirigami.Heading {
                            level: 3
                            text: i18n("Wallpaper")
                        }
                        Item { Layout.fillWidth: true }
                        Kirigami.IconButton {
                            icon.source: "view-refresh"
                            onClicked: mainController.wallpaper.refresh()
                            tooltip: i18n("Refresh wallpaper list")
                        }
                    }

                    // Current wallpaper preview
                    Item {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 120
                        visible: mainController.wallpaper.currentWallpaper !== ""

                        Image {
                            id: wallpaperPreview
                            source: mainController.wallpaper.currentWallpaper
                            fillMode: Image.PreserveAspectCrop
                            anchors.fill: parent
                            layer.enabled: true
                            layer.effect: FastBlur {
                                radius: 8
                                transparentBorder: true
                            }
                        }

                        Rectangle {
                            anchors.fill: parent
                            color: "transparent"
                            border.color: Kirigami.Theme.highlightColor
                            border.width: 2
                            radius: 8
                        }

                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            onEntered: wallpaperPreview.layer.effect.radius = 0
                            onExited: wallpaperPreview.layer.effect.radius = 8
                        }
                    }

                    // Wallpaper controls
                    RowLayout {
                        spacing: Kirigami.Units.mediumSpacing

                        Kirigami.Button {
                            Layout.fillWidth: true
                            text: i18n("Previous")
                            icon.source: "go-previous"
                            onClicked: mainController.wallpaper.prevWallpaper()
                        }

                        Kirigami.Button {
                            Layout.fillWidth: true
                            text: i18n("Pick Wallpaper...")
                            icon.source: "image-x-generic"
                            highlighted: true
                            onClicked: mainController.wallpaper.pickWallpaper()
                        }

                        Kirigami.Button {
                            Layout.fillWidth: true
                            text: i18n("Next")
                            icon.source: "go-next"
                            onClicked: mainController.wallpaper.nextWallpaper()
                        }
                    }

                    // Hint about alternative methods
                    Kirigami.Separator {}

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Kirigami.Heading {
                            level: 4
                            text: i18n("Alternative ways to change wallpaper:")
                        }

                        Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            text: i18n(
                                "• Right-click desktop → Configure Desktop & Wallpaper\n" +
                                "• System Settings → Appearance → Wallpaper\n" +
                                "• Terminal: <tt>wallpaper-picker</tt>, <tt>wallpaper-next</tt>, <tt>wallpaper-prev</tt>"
                            )
                            font.pointSize: Kirigami.Units.fontSizes.small
                            color: Kirigami.Theme.textColor
                            opacity: 0.7
                        }
                    }
                }
            }
        }

        // ─── Actions ───
        actions.main: Kirigami.Action {
            text: i18n("Settings")
            icon.name: "configure"
            onTriggered: pageStack.push(Qt.resolvedUrl("SettingsPage.qml"))
        }

        actions.main: Kirigami.Action {
            text: i18n("Quit")
            icon.name: "application-exit"
            onTriggered: Qt.quit()
        }
    }

    // ─── Dialogs ───
    Kirigami.Dialog {
        id: confirmDialog
        title: i18n("Confirm")
        standardButtons: Kirigami.Dialog.Ok | Kirigami.Dialog.Cancel
        onAccepted: mainController.profile.deleteProfile(confirmDialog.property("targetProfile"))
        property string targetProfile: ""
    }

    Kirigami.Dialog {
        id: saveDialog
        title: i18n("Save Profile")
        standardButtons: Kirigami.Dialog.Ok | Kirigami.Dialog.Cancel
        property string newProfileName: ""

        ColumnLayout {
            Layout.fillWidth: true
            Layout.minimumWidth: 300
            TextField {
                id: nameField
                Layout.fillWidth: true
                placeholderText: i18n("Profile name")
                onTextChanged: saveDialog.newProfileName = text
            }
        }
        onAccepted: {
            if (nameField.text.trim()) {
                mainController.profile.saveProfile(nameField.text.trim())
                nameField.text = ""
            }
        }
    }

    Kirigami.Dialog {
        id: diffDialog
        title: i18n("Profile Diff")
        standardButtons: Kirigami.Dialog.Close
        property string profileA: ""
        property string profileB: ""

        Kirigami.ScrollablePage {
            Layout.minimumWidth: 500
            Layout.minimumHeight: 400
            TextEdit {
                id: diffText
                Layout.fillWidth: true
                Layout.fillHeight: true
                readOnly: true
                font.family: "Monospace"
                font.pointSize: Kirigami.Units.fontSizes.small
                wrapMode: TextEdit.NoWrap
            }
        }
        onProfileAChanged: updateDiff()
        onProfileBChanged: updateDiff()

        function updateDiff() {
            if (profileA && profileB) {
                diffText.text = mainController.profile.diffProfiles(profileA, profileB)
            }
        }
    }

    function showSaveDialog() {
        saveDialog.open()
    }

    // ─── Theme handling (dogfooding) ───
    Component.onCompleted: {
        mainController.initialize()
    }
}