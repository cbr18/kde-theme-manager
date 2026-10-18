import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami
import org.kde.kirigami.platform as Platform
import Components 1.0

Kirigami.ApplicationWindow {
    id: root

    title: qsTr("Theme Profile Manager")
    width: 820
    height: 680
    minimumWidth: 640
    minimumHeight: 480

    // ──────────────────────────────────────────────────────────────
    // Helpers
    // ──────────────────────────────────────────────────────────────
    // Kirigami.Theme colors can be invalid with PySide6's bundled Qt
    // combined with the system Kirigami plugin → always keep a fallback.
    function safeColor(role, fallback) {
        var c = Kirigami.Theme[role]
        return (c && c.valid) ? c : fallback
    }

    // Dogfooding: follow the active profile (glass → translucent).
    readonly property bool glassMode: themeController.isGlass

    readonly property color cardBg: glassMode
        ? Qt.rgba(1, 1, 1, 0.09)
        : safeColor("viewColor", "#ffffff")
    // Borders are derived from the foreground with a low alpha so they stay
    // visible in both themes (Kirigami's viewColor is always white here).
    readonly property color cardBorder: glassMode
        ? Qt.rgba(1, 1, 1, 0.18)
        : Qt.rgba(0.15, 0.15, 0.15, 0.18)
    readonly property color fgColor: glassMode
        ? "#ffffff"
        : safeColor("textColor", "#1f1f1f")
    readonly property color dimColor: glassMode
        ? Qt.rgba(1, 1, 1, 0.80)
        : Qt.rgba(0.15, 0.15, 0.15, 0.65)

    // The window surface itself stays transparent in glass mode: the page
    // paints the translucent glass panel on top (see mainPage.background).
    color: glassMode ? "transparent" : safeColor("backgroundColor", "#eff0f3")

    // Profile the user picked in the UI. Applying is explicit (Apply button)
    // because switching profiles is expensive — the user may want to look
    // around before committing.
    property string selectedProfile: ""

    Connections {
        target: profileController
        function onActiveProfileChanged() {
            if (root.selectedProfile === "") {
                root.selectedProfile = profileController.activeProfile
            }
        }
    }

    Component.onCompleted: {
        themeController.set_window(root)
        profileController.refresh()
        wallpaperController.refresh()
        trackedAppsController.refresh()
        settingsController.load()
    }

    // ──────────────────────────────────────────────────────────────
    // Main page
    // NOTE: ScrollablePage IS the page — its single child must be a
    // layout (children are only anchored left/right, not laid out).
    // ──────────────────────────────────────────────────────────────
    pageStack.initialPage: Kirigami.ScrollablePage {
        id: mainPage
        title: qsTr("Theme Profiles")

        // Kirigami.Page paints Platform.Theme.backgroundColor behind its
        // content. In glass mode we paint a translucent dark "glass panel"
        // ourselves so the window tint is guaranteed regardless of whether
        // the compositor applies blur/alpha to the surface.
        background: Rectangle {
            color: root.glassMode
                ? Qt.rgba(0.09, 0.10, 0.12, 0.72)
                : root.safeColor("backgroundColor", "#eff0f3")
        }

        ColumnLayout {
            spacing: Platform.Units.largeSpacing
            Layout.margins: Platform.Units.largeSpacing

            // ─── Active Profile ───
            Kirigami.Card {
                Layout.fillWidth: true

                background: Rectangle {
                    color: root.cardBg
                    radius: Platform.Units.smallSpacing
                    border.width: 1
                    border.color: root.cardBorder
                }

                contentItem: ColumnLayout {
                    spacing: Platform.Units.mediumSpacing

                    RowLayout {
                        Layout.fillWidth: true

                        Kirigami.Heading {
                            level: 2
                            text: qsTr("Active Profile")
                            color: root.fgColor
                        }
                        Item { Layout.fillWidth: true }
                        Button {
                            text: qsTr("Refresh")
                            icon.name: "view-refresh"
                            onClicked: profileController.refresh()
                        }
                        Button {
                            text: qsTr("Apply")
                            icon.name: "dialog-ok-apply"
                            highlighted: true
                            enabled: root.selectedProfile !== ""
                                && root.selectedProfile !== profileController.activeProfile
                            onClicked: profileController.applyProfile(root.selectedProfile)
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Platform.Units.mediumSpacing

                        Repeater {
                            model: profileController.profiles.length

                            delegate: ProfileRadioButton {
                                readonly property var entry: profileController.profiles[index]
                                glassMode: root.glassMode
                                profileName: entry ? entry.name : ""
                                isActive: entry ? entry.isActive : false
                                selected: entry ? root.selectedProfile === entry.name : false
                                componentCount: entry ? entry.componentCount : 0
                                onProfileClicked: root.selectedProfile = profileName
                            }
                        }

                        Item { Layout.fillWidth: true }
                    }

                    Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        color: root.dimColor
                        font.pointSize: Platform.Units.smallSpacing
                        text: {
                            if (root.selectedProfile === "")
                                return qsTr("Select a profile above, then press Apply.")
                            if (root.selectedProfile === profileController.activeProfile)
                                return qsTr("Active profile: %1").arg(root.selectedProfile)
                            return qsTr("Selected \"%1\" (not applied yet). Active: %2")
                                .arg(root.selectedProfile)
                                .arg(profileController.activeProfile)
                        }
                    }
                }
            }

            // ─── Available Profiles ───
            Kirigami.Card {
                Layout.fillWidth: true

                background: Rectangle {
                    color: root.cardBg
                    radius: Platform.Units.smallSpacing
                    border.width: 1
                    border.color: root.cardBorder
                }

                contentItem: ColumnLayout {
                    spacing: Platform.Units.mediumSpacing

                    RowLayout {
                        Layout.fillWidth: true

                        Kirigami.Heading {
                            level: 2
                            text: qsTr("Available Profiles")
                            color: root.fgColor
                        }
                        Item { Layout.fillWidth: true }
                        Button {
                            text: qsTr("Save current…")
                            icon.name: "list-add"
                            onClicked: saveDialog.open()
                        }
                    }

                    Repeater {
                        model: profileController.profiles.length

                        delegate: ProfileCardDelegate {
                            readonly property var entry: profileController.profiles[index]
                            glassMode: root.glassMode
                            profileName: entry ? entry.name : ""
                            profileIsActive: entry ? entry.isActive : false
                            profileComponentCount: entry ? entry.componentCount : 0
                            profileComponents: entry ? entry.components : []

                            onApplyClicked: profileController.applyProfile(profileName)
                            onPreviewClicked: {
                                previewDialog.previewProfile = profileName
                                previewDialog.activeProfile = profileController.activeProfile
                                previewDialog.open()
                            }
                            onDiffClicked: {
                                diffDialog.profileA = profileName
                                diffDialog.profileB = profileController.activeProfile
                                diffDialog.updateDiff()
                                diffDialog.open()
                            }
                            onDeleteClicked: {
                                confirmDialog.targetProfile = profileName
                                confirmDialog.open()
                            }
                        }
                    }

                    Label {
                        Layout.fillWidth: true
                        visible: profileController.profiles.length === 0
                        text: qsTr("No profiles found. Save the current theme to create one.")
                        color: root.dimColor
                        wrapMode: Text.WordWrap
                    }
                }
            }

            // ─── Wallpaper ───
            Kirigami.Card {
                Layout.fillWidth: true

                background: Rectangle {
                    color: root.cardBg
                    radius: Platform.Units.smallSpacing
                    border.width: 1
                    border.color: root.cardBorder
                }

                contentItem: ColumnLayout {
                    spacing: Platform.Units.mediumSpacing

                    RowLayout {
                        Layout.fillWidth: true

                        Kirigami.Heading {
                            level: 2
                            text: qsTr("Wallpaper")
                            color: root.fgColor
                        }
                        Item { Layout.fillWidth: true }
                        Button {
                            text: qsTr("Refresh")
                            icon.name: "view-refresh"
                            onClicked: wallpaperController.refresh()
                        }
                    }

                    Item {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 160
                        visible: wallpaperController.currentWallpaper !== ""

                        Image {
                            anchors.fill: parent
                            source: wallpaperController.currentWallpaper
                            fillMode: Image.PreserveAspectCrop
                        }

                        Rectangle {
                            anchors.fill: parent
                            color: "transparent"
                            radius: 8
                            border.width: 1
                            border.color: root.cardBorder
                        }
                    }

                    Label {
                        visible: wallpaperController.currentWallpaper === ""
                        text: qsTr("No wallpaper information available.")
                        color: root.dimColor
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Platform.Units.mediumSpacing

                        Button {
                            Layout.fillWidth: true
                            text: qsTr("Previous")
                            icon.name: "go-previous-view"
                            onClicked: wallpaperController.prevWallpaper()
                        }
                        Button {
                            Layout.fillWidth: true
                            text: qsTr("Pick Wallpaper…")
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
                }
            }
        }
    }

    // ──────────────────────────────────────────────────────────────
    // Dialogs
    // ──────────────────────────────────────────────────────────────
    Kirigami.Dialog {
        id: confirmDialog
        title: qsTr("Delete Profile")
        standardButtons: Kirigami.Dialog.Ok | Kirigami.Dialog.Cancel
        preferredWidth: 380
        property string targetProfile: ""

        ColumnLayout {
            Layout.fillWidth: true
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: qsTr("Delete profile \"%1\"? This cannot be undone.").arg(confirmDialog.targetProfile)
            }
        }

        onAccepted: {
            if (confirmDialog.targetProfile !== "") {
                profileController.deleteProfile(confirmDialog.targetProfile)
            }
        }
    }

    Kirigami.Dialog {
        id: saveDialog
        title: qsTr("Save Profile")
        standardButtons: Kirigami.Dialog.Ok | Kirigami.Dialog.Cancel
        preferredWidth: 420

        ColumnLayout {
            Layout.fillWidth: true
            Label { text: qsTr("Save the current theme as a new profile:") }
            TextField {
                id: nameField
                Layout.fillWidth: true
                placeholderText: qsTr("Profile name")
            }
        }

        onAccepted: {
            if (nameField.text.trim() !== "") {
                profileController.saveProfile(nameField.text.trim())
                nameField.text = ""
            }
        }
    }

    Kirigami.Dialog {
        id: diffDialog
        title: qsTr("Profile Diff")
        standardButtons: Kirigami.Dialog.Close
        preferredWidth: 640
        preferredHeight: 480
        property string profileA: ""
        property string profileB: ""

        function updateDiff() {
            if (profileA !== "" && profileB !== "" && profileA !== profileB) {
                diffText.text = profileController.diffProfiles(profileA, profileB)
            } else if (profileA === profileB) {
                diffText.text = qsTr("No differences: both profiles are \"%1\".").arg(profileA)
            } else {
                diffText.text = qsTr("No active profile to compare with.")
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: qsTr("Difference between \"%1\" and \"%2\":").arg(diffDialog.profileA).arg(diffDialog.profileB)
                font.bold: true
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredHeight: 360
                clip: true

                TextEdit {
                    id: diffText
                    readOnly: true
                    font.family: "monospace"
                    wrapMode: TextEdit.NoWrap
                }
            }
        }
    }

    Kirigami.Dialog {
        id: previewDialog
        title: qsTr("Preview Profile Changes")
        standardButtons: Kirigami.Dialog.Ok | Kirigami.Dialog.Cancel
        preferredWidth: 640
        preferredHeight: 520
        property string previewProfile: ""
        property string activeProfile: ""
        property var componentsToApply: []
        property string diffContent: ""

        onPreviewProfileChanged: {
            if (previewDialog.previewProfile !== "" && previewDialog.activeProfile !== "") {
                var comps = profileController.getProfileComponents(previewDialog.previewProfile)
                var list = []
                for (var i = 0; i < comps.length; i++) {
                    list.push(comps[i])
                }
                previewDialog.componentsToApply = list
                previewDialog.diffContent = profileController.diffProfiles(
                    previewDialog.activeProfile, previewDialog.previewProfile)
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Platform.Units.mediumSpacing

            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: qsTr("Applying \"%1\" will change the following components:").arg(previewDialog.previewProfile)
            }

            Flow {
                Layout.fillWidth: true
                spacing: 4
                Repeater {
                    model: previewDialog.componentsToApply
                    delegate: Kirigami.Chip {
                        text: modelData
                        closable: false
                    }
                }
            }

            Label {
                Layout.fillWidth: true
                text: qsTr("Diff against active profile:")
                font.bold: true
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredHeight: 280
                clip: true

                TextEdit {
                    readOnly: true
                    font.family: "monospace"
                    wrapMode: TextEdit.NoWrap
                    text: previewDialog.diffContent
                }
            }
        }

        onAccepted: profileController.applyProfile(previewDialog.previewProfile)
    }
}
