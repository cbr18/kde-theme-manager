import QtQuick
import org.kde.kirigami.platform as Platform
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami

Kirigami.Card {
    id: group
    Layout.fillWidth: true
    property string category: ""
    property var selectedComponents: []
    property var availableComponents: []

    // Local selection state (mirrors selectedComponents but mutable)
    property var _localSelection: []

    Component.onCompleted: {
        _localSelection = selectedComponents.slice()
    }

    onSelectedComponentsChanged: {
        _localSelection = selectedComponents.slice()
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: Platform.Units.smallSpacing

        // Category header
        RowLayout {
            Layout.fillWidth: true

            Kirigami.Icon {
                source: categoryIcon(category)
                Layout.preferredWidth: Platform.Units.iconSizes.medium
                Layout.preferredHeight: Platform.Units.iconSizes.medium
                color: Kirigami.Theme.highlightColor
            }

            Kirigami.Heading {
                level: 3
                text: category
            }

            Item { Layout.fillWidth: true }

            Kirigami.ToolButton {
                id: expandBtn
                icon.source: expanded ? "go-up" : "go-down"
                onClicked: expanded = !expanded
            }
        }

        Kirigami.Separator {}

        // Components list (collapsible)
        ColumnLayout {
            id: componentsLayout
            Layout.fillWidth: true
            spacing: Platform.Units.smallSpacing
            visible: expanded
            height: expanded ? implicitHeight : 0

            Repeater {
                id: repeater
                model: mainController.tracked_apps.getComponentsByCategory(category)
                delegate: ComponentCheckbox {
                    componentId: model.id
                    componentName: model.name
                    componentStatus: model.status
                    componentStatusText: model.statusText
                    componentDescription: model.description
                    componentIcon: model.icon
                    componentSupportsLiveReload: model.supportsLiveReload
                    isSelected: _localSelection.indexOf(model.id) !== -1
                    isAvailable: availableComponents.indexOf(model.id) !== -1
                    onToggled: {
                        var idx = _localSelection.indexOf(componentId)
                        if (checked && idx === -1) {
                            _localSelection.push(componentId)
                        } else if (!checked && idx !== -1) {
                            _localSelection.splice(idx, 1)
                        }
                        // Update the bound property
                        group.selectedComponents = _localSelection.slice()
                        selectionChanged()
                    }
                }
            }
        }

        Behavior on componentsLayout.height {
            NumberAnimation { duration: 200; easing.type: Easing.OutCubic }
        }
    }

    property bool expanded: true

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
            "System Profiles": "preferences-desktop-theme",
        }
        return icons[cat] || "application-x-executable"
    }

    signal selectionChanged()
}