import QtQuick
import org.kde.kirigami.platform as Platform
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami

Kirigami.AbstractCard {
    id: card

    Layout.preferredWidth: Platform.Units.gridUnit * 11
    Layout.minimumWidth: Platform.Units.gridUnit * 9
    Layout.maximumWidth: Platform.Units.gridUnit * 16

    property string profileName: ""
    // isActive: profile currently applied to the system
    property bool isActive: false
    // selected: profile the user picked (not applied yet)
    property bool selected: false
    property int componentCount: 0
    property bool glassMode: false

    readonly property string displayName: profileName === "glass" ? qsTr("Glass")
        : profileName === "paper" ? qsTr("Paper")
        : profileName

    signal profileClicked(string profileName)

    // Whole card is the click/keyboard target.
    activeFocusOnTab: true
    Keys.onSpacePressed: card.profileClicked(card.profileName)
    Keys.onReturnPressed: card.profileClicked(card.profileName)
    Keys.onEnterPressed: card.profileClicked(card.profileName)

    TapHandler {
        onTapped: card.profileClicked(card.profileName)
    }

    HoverHandler { id: hover }

    // Slightly brighten the singleton border colour (glass borders are
    // transparent white, so Qt.lighter() would be a no-op).
    function brighten(c) {
        return Qt.rgba(c.r, c.g, c.b, Math.min(1, c.a * 2))
    }

    contentItem: ColumnLayout {
        spacing: 2

        RowLayout {
            Layout.fillWidth: true
            spacing: Platform.Units.smallSpacing

            RadioButton {
                id: radio
                Layout.fillWidth: true
                checked: card.selected
                // A QQC2 control writes to `checked` on click, which would
                // destroy the binding above and let two radios look checked
                // at once. Re-arm it so the model stays authoritative.
                Binding {
                    target: radio
                    property: "checked"
                    value: card.selected
                    restoreMode: Binding.RestoreBindingOrValue
                }
                autoExclusive: false
                activeFocusOnTab: false
                enabled: card.enabled
                text: card.displayName
                font.bold: card.isActive
                onClicked: card.profileClicked(card.profileName)
                // `toggled` only fires for user interaction, so this can never
                // fight the Binding above (which only re-arms on model change).
                // It closes the window where clicking an unselected radio set
                // `checked` by hand before the model caught up.
                onToggled: radio.checked = card.selected
                palette.windowText: ThemeColors.fgColor(card.glassMode)
                palette.text: ThemeColors.fgColor(card.glassMode)
            }

            Kirigami.Icon {
                visible: card.isActive
                source: "dialog-ok-apply"
                color: ThemeColors.positive()
                Layout.preferredWidth: 18
                Layout.preferredHeight: 18
                Layout.alignment: Qt.AlignVCenter
            }
        }

        Label {
            Layout.leftMargin: Platform.Units.iconSizes.small
            text: qsTr("%1 components").arg(card.componentCount)
            font.pointSize: TypeScale.caption
            color: ThemeColors.dimColor(card.glassMode)
        }

        Label {
            Layout.leftMargin: Platform.Units.iconSizes.small
            visible: card.isActive
            text: qsTr("Active now")
            font.pointSize: TypeScale.caption
            // Slightly lighter in glass mode: the dark translucent panel eats
            // most of the contrast of the mid-tone positive colour.
            color: card.glassMode
                ? Qt.lighter(ThemeColors.positive(), 1.35)
                : ThemeColors.positive()
        }

        Label {
            Layout.leftMargin: Platform.Units.iconSizes.small
            visible: !card.isActive && card.selected
            text: qsTr("Press Apply to use")
            font.pointSize: TypeScale.caption
            color: card.glassMode
                ? Qt.lighter(ThemeColors.accent(), 1.35)
                : ThemeColors.accent()
        }
    }

    background: Rectangle {
        radius: 8
        border.width: (card.isActive || card.selected) ? 2 : 1
        border.color: card.activeFocus ? ThemeColors.accent()
            : card.isActive ? ThemeColors.positive()
            : card.selected ? ThemeColors.accent()
            : hover.hovered ? card.brighten(ThemeColors.cardBorder(card.glassMode))
            : ThemeColors.cardBorder(card.glassMode)
        // The accent/positive fill tint used to be here, but green-on-green
        // ("Active now" in positive text over a positive tint) and
        // accent-on-accent were barely readable. The 2 px coloured border plus
        // the check icon already carry the state, so the fill stays neutral.
        color: card.glassMode ? ThemeColors.nestedBg(card.glassMode) : "transparent"

        Behavior on border.color { ColorAnimation { duration: 150 } }
        Behavior on color { ColorAnimation { duration: 150 } }
    }
}
