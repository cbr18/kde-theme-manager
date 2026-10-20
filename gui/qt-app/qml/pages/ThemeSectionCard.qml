import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami
import org.kde.kirigami.platform as Platform
import Components 1.0

/*! Collapsible overview card for one theme section. */
Kirigami.AbstractCard {
    id: card

    property var sectionData: ({})
    property bool expanded: false
    property bool glassMode: false
    property bool showAdvanced: false

    signal toggleRequested()

    Layout.fillWidth: true

    contentItem: ColumnLayout {
        spacing: Platform.Units.smallSpacing

        Item {
            Layout.fillWidth: true
            implicitHeight: header.implicitHeight

            RowLayout {
                id: header
                anchors.fill: parent
                spacing: Platform.Units.mediumSpacing

                Kirigami.Icon {
                    source: card.sectionData.icon || "preferences-desktop-theme"
                    Layout.preferredWidth: Platform.Units.iconSizes.medium
                    Layout.preferredHeight: Platform.Units.iconSizes.medium
                    color: ThemeColors.accent()
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0

                    Label {
                        text: card.sectionData.title || ""
                        color: ThemeColors.fgColor(card.glassMode)
                        font.bold: true
                        font.pointSize: TypeScale.subtitle
                    }

                    Label {
                        Layout.fillWidth: true
                        text: card.sectionData.summary || card.sectionData.description || ""
                        color: ThemeColors.dimColor(card.glassMode)
                        font.pointSize: TypeScale.caption
                        elide: Text.ElideRight
                    }
                }

                Rectangle {
                    visible: (card.sectionData.issueCount || 0) > 0
                    radius: height / 2
                    color: ThemeColors.warning()
                    implicitWidth: issueLabel.implicitWidth + 10
                    implicitHeight: issueLabel.implicitHeight + 2

                    Label {
                        id: issueLabel
                        anchors.centerIn: parent
                        text: card.sectionData.issueCount || 0
                        color: "black"
                        font.pointSize: TypeScale.caption
                        font.bold: true
                    }
                }

                ToolButton {
                    icon.name: card.expanded ? "go-up" : "go-down"
                    ToolTip.text: card.expanded ? qsTr("Collapse") : qsTr("Expand")
                    ToolTip.visible: hovered
                    onClicked: card.toggleRequested()
                }
            }

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton
                z: -1
                onClicked: card.toggleRequested()
            }
        }

        Kirigami.Separator {
            Layout.fillWidth: true
            visible: card.expanded
        }

        ThemeSectionFields {
            Layout.fillWidth: true
            visible: card.expanded
            sectionId: card.sectionData.id || ""
            glassMode: card.glassMode
            showAdvanced: card.showAdvanced
        }
    }

    background: Rectangle {
        radius: Platform.Units.smallSpacing
        border.width: 1
        color: ThemeColors.cardBg(card.glassMode)
        border.color: card.expanded
            ? ThemeColors.accent()
            : ThemeColors.cardBorder(card.glassMode)
    }
}
