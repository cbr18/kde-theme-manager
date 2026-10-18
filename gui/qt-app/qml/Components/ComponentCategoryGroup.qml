import QtQuick
import org.kde.kirigami.platform as Platform
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami

Kirigami.Card {
    id: group

    // Fallback colors for PySide6 bundled Qt
    function safeColor(role, fallback) {
        var c = Kirigami.Theme[role]
        return c && c.valid ? c : fallback
    }

    function categoryIcon(cat) {
        const icons = {
            "KDE / Plasma": "plasma",
            "GTK / Qt": "preferences-desktop-theme-gtk",
            "Window Decorations": "preferences-system-windows",
            "Terminals": "utilities-terminal",
            "Launchers / Menu": "system-run",
            "Monitors": "utilities-system-monitor",
            "Sysinfo": "preferences-desktop-theme",
            "Editors": "text-editor",
            "Browser": "web-browser",
            "Notes": "x-office-note",
            "System Profiles": "preferences-desktop-theme"
        }
        return icons[cat] || "application-x-executable"
    }

    Layout.fillWidth: true
    property string category: ""
    property var selectedComponents: []
    property var availableComponents: []
    property bool glassMode: false
    property bool expanded: true

    readonly property color fgColor: glassMode ? "#ffffff" : safeColor("textColor", "#1f1f1f")

    // Local selection state (mirrors selectedComponents but mutable)
    property var _localSelection: []

    signal selectionChanged()

    onSelectedComponentsChanged: _localSelection = selectedComponents.slice()
    Component.onCompleted: _localSelection = selectedComponents.slice()

    contentItem: ColumnLayout {
        spacing: Platform.Units.smallSpacing

        // Category header
        RowLayout {
            Layout.fillWidth: true

            Kirigami.Icon {
                source: group.categoryIcon(group.category)
                Layout.preferredWidth: Platform.Units.iconSizes.medium
                Layout.preferredHeight: Platform.Units.iconSizes.medium
                color: group.safeColor("highlightColor", "#2980b9")
            }

            Kirigami.Heading {
                level: 3
                text: group.category
                color: group.fgColor
            }

            Item { Layout.fillWidth: true }

            Kirigami.ToolButton {
                icon.source: group.expanded ? "go-up" : "go-down"
                onClicked: group.expanded = !group.expanded
            }
        }

        Kirigami.Separator {}

        // Components list (collapsible)
        ColumnLayout {
            id: componentsLayout
            Layout.fillWidth: true
            spacing: Platform.Units.smallSpacing
            visible: group.expanded
            height: group.expanded ? implicitHeight : 0

            Repeater {
                model: mainController.tracked_apps.getComponentsByCategory(group.category)
                delegate: ComponentCheckbox {
                    glassMode: group.glassMode
                    componentId: model.id
                    componentName: model.name
                    componentStatus: model.status
                    componentStatusText: model.statusText
                    componentDescription: model.description
                    componentIcon: model.icon
                    componentSupportsLiveReload: model.supportsLiveReload
                    isSelected: group._localSelection.indexOf(model.id) !== -1
                    isAvailable: group.availableComponents.indexOf(model.id) !== -1
                    onToggled: {
                        var idx = group._localSelection.indexOf(componentId)
                        if (checked && idx === -1) {
                            group._localSelection.push(componentId)
                        } else if (!checked && idx !== -1) {
                            group._localSelection.splice(idx, 1)
                        }
                        group.selectedComponents = group._localSelection.slice()
                        group.selectionChanged()
                    }
                }
            }
        }

        Behavior on componentsLayout.height {
            NumberAnimation { duration: 200; easing.type: Easing.OutCubic }
        }
    }

    background: Rectangle {
        radius: 6
        border.width: 1
        color: group.glassMode ? Qt.rgba(1, 1, 1, 0.08) : group.safeColor("viewColor", "#ffffff")
        border.color: group.glassMode
            ? Qt.rgba(1, 1, 1, 0.18)
            : Qt.rgba(0.15, 0.15, 0.15, 0.18)
    }
}
