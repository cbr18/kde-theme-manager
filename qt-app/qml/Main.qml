import QtQuick
import QtQuick.Controls
import QtQuick.Controls 2.15
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami
import org.kde.kirigami.platform as Platform
import QtQml.Models 2.1
import Components 1.0
import QtQuick.Controls.Basic

Kirigami.ApplicationWindow {
    id: root
    title: qsTr("Theme Profile Manager")
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
        title: qsTr("Theme Profiles")

        Kirigami.ScrollablePage {

            // ─── Header: Active Profile ───
            Kirigami.Card {
                Layout.fillWidth: true
                Layout.leftMargin: Platform.Units.largeSpacing
                Layout.rightMargin: Platform.Units.largeSpacing
                Layout.topMargin: Platform.Units.largeSpacing

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Platform.Units.smallSpacing

                    RowLayout {
                        Layout.fillWidth: true
                        Kirigami.Heading {
                            level: 2
                            text: qsTr("Active Profile")
                        }
                        Item { Layout.fillWidth: true }
                        Button {
                            icon.name: "view-refresh"
                            flat: true
                            onClicked: profileController.refresh()
                        }
                    }

                    RowLayout {
    spacing: Platform.Units.mediumSpacing
    Repeater {
        model: profileController.profiles
        delegate: ProfileRadioButton {
            profileName: model.name
            isActive: model.isActive
            componentCount: model.componentCount
            onProfileClicked: {
                if (!model.isActive) {
                    profileController.applyProfile(model.name)
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
                Layout.leftMargin: Platform.Units.largeSpacing
                Layout.rightMargin: Platform.Units.largeSpacing
                Layout.topMargin: Platform.Units.mediumSpacing

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Platform.Units.smallSpacing

                    RowLayout {
                        Kirigami.Heading {
                            level: 3
                            text: qsTr("Available Profiles")
                        }
                        Item { Layout.fillWidth: true }
                        Button {
                            icon.name: "list-add"
                            flat: true
                            onClicked: showSaveDialog()
                        }
                    }

                    Kirigami.CardsListView {
                        Layout.fillWidth: true
                        Layout.minimumHeight: 180
                        model: profileController.profiles
                        delegate: ProfileCardDelegate {
                            onApplyClicked: profileController.applyProfile(model.name)
                            onDeleteClicked: {
                                if (settingsController.confirmBeforeApply) {
                                    confirmDialog.text = qsTr("Delete profile \"%1\"?", model.name)
                                    confirmDialog.open()
                                } else {
                                    profileController.deleteProfile(model.name)
                                }
                            }
                            onDiffClicked: {
                                diffDialog.profileA = model.name
                                diffDialog.profileB = profileController.activeProfile
                                diffDialog.open()
                            }
                        }
                    }
                }
            }

            // ─── Wallpaper Section ───
            Kirigami.Card {
                Layout.fillWidth: true
                Layout.leftMargin: Platform.Units.largeSpacing
                Layout.rightMargin: Platform.Units.largeSpacing
                Layout.topMargin: Platform.Units.mediumSpacing
                Layout.bottomMargin: Platform.Units.largeSpacing

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Platform.Units.smallSpacing

                    RowLayout {
                        Kirigami.Heading {
                            level: 3
                            text: qsTr("Wallpaper")
                        }
                        Item { Layout.fillWidth: true }
                        Button {
                            icon.name: "view-refresh"
                            flat: true
                            onClicked: wallpaperController.refresh()
                        }
                    }

                    // Current wallpaper preview
                    Item {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 120
                        visible: wallpaperController.currentWallpaper !== ""

                        Image {
                            id: wallpaperPreview
                            source: wallpaperController.currentWallpaper
                            fillMode: Image.PreserveAspectCrop
                            anchors.fill: parent
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
                        spacing: Platform.Units.mediumSpacing

                        Button {
                            Layout.fillWidth: true
                            text: qsTr("Previous")
                            icon.name: "go-previous-view"
                            onClicked: wallpaperController.prevWallpaper()
                        }

                        Button {
                            Layout.fillWidth: true
                            text: qsTr("Pick Wallpaper...")
                            icon.name: "image-x-generic"
                            highlighted: true
                            onClicked: wallpaperController.pickWallpaper()
                        }

                        Button {
                            Layout.fillWidth: true
                            text: qsTr("Next")
                            icon.name: "go-next-view"
                            onClicked: wallpaperController.nextWallpaper()
                        }
                    }

                    // Hint about alternative methods
                    Kirigami.Separator {}

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Kirigami.Heading {
                            level: 4
                            text: qsTr("Alternative ways to change wallpaper:")
                        }

                        Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            text: qsTr(
                                "• Right-click desktop → Configure Desktop & Wallpaper\n" +
                                "• System Settings → Appearance → Wallpaper\n" +
                                "• Terminal: <tt>wallpaper-picker</tt>, <tt>wallpaper-next</tt>, <tt>wallpaper-prev</tt>"
                            )
                            font.pointSize: Platform.Units.smallSpacing
                            color: Kirigami.Theme.textColor
                            opacity: 0.7
                        }
                    }
                }
            }
        }

        // ─── Actions ───
        // actions handled via header buttons
    }

    // ─── Dialogs ───
    Kirigami.Dialog {
        id: confirmDialog
        title: qsTr("Confirm")
        standardButtons: Kirigami.Dialog.Ok | Kirigami.Dialog.Cancel
        onAccepted: profileController.deleteProfile(confirmDialog.property("targetProfile"))
        property string targetProfile: ""
    }

    Kirigami.Dialog {
        id: saveDialog
        title: qsTr("Save Profile")
        standardButtons: Kirigami.Dialog.Ok | Kirigami.Dialog.Cancel
        property string newProfileName: ""

        ColumnLayout {
            Layout.fillWidth: true
            Layout.minimumWidth: 300
            TextField {
                id: nameField
                Layout.fillWidth: true
                placeholderText: qsTr("Profile name")
                onTextChanged: saveDialog.newProfileName = text
            }
        }
        onAccepted: {
            if (nameField.text.trim()) {
                profileController.saveProfile(nameField.text.trim())
                nameField.text = ""
            }
        }
    }

    Kirigami.Dialog {
        id: diffDialog
        title: qsTr("Profile Diff")
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
                font.pointSize: Platform.Units.smallSpacing
                wrapMode: TextEdit.NoWrap
            }
        }
        onProfileAChanged: updateDiff()
        onProfileBChanged: updateDiff()

        function updateDiff() {
            if (profileA && profileB) {
                diffText.text = profileController.diffProfiles(profileA, profileB)
            }
        }
    }

    function showSaveDialog() {
        saveDialog.open()
    }

    // ─── Theme handling (dogfooding) ───
    Component.onCompleted: {
        profileController.refresh()
wallpaperController.refresh()
trackedAppsController.refresh()
settingsController.load()
    }
}