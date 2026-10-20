import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami 2.20 as Kirigami
import org.kde.kirigami.platform as Platform
import Components 1.0

/*! All rows of one inspector section (live values or a profile snapshot). */
ColumnLayout {
    id: root

    property string sectionId: ""
    property bool glassMode: false
    property bool showAdvanced: false
    property var fields: []

    Layout.fillWidth: true
    spacing: Platform.Units.smallSpacing

    function reload() {
        fields = root.visible ? themeInspector.fieldsFor(sectionId) : []
    }

    Component.onCompleted: reload()
    onVisibleChanged: reload()

    Connections {
        target: themeInspector
        function onFieldsChanged() { root.reload() }
    }

    Repeater {
        model: root.fields

        delegate: ThemeFieldRow {
            fieldData: modelData
            visible: root.showAdvanced || !modelData.advanced
            glassMode: root.glassMode
        }
    }

    Label {
        Layout.fillWidth: true
        visible: root.fields.length === 0
        text: qsTr("No fields in this section.")
        color: ThemeColors.dimColor(root.glassMode)
    }
}
