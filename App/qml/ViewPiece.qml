import QtQuick 2.13
import QtQuick.Controls 2.13
import QtQuick.Layouts 1.12
import Backend 1.0

Item {
    RowLayout {
        anchors.fill: parent
	spacing: 0

	ColumnLayout {
            Layout.fillWidth: true

            FigureToolbar {
                id: mplView
                objectName : "viewpiece"
                            
                Layout.fillWidth: true
                Layout.fillHeight: true
                
                Layout.minimumWidth: 10
                Layout.minimumHeight: 10
            }
            


	    // En er iets onder
	    Text {
		width: 400
                Layout.minimumHeight: 50
		text: 'View piece links onder'
	    }

	}

      Connections {
            target: sensorModel2
            onDataChanged: {
                piece_mpl.update_figure()
            }
      }

        Pane {
            id: right
            Layout.alignment: Qt.AlignLeft | Qt.AlignTop
            Layout.fillHeight: true
	    
            ColumnLayout {
                id: right_vbox
                spacing: 2
                
                Label {
                    id: log_label
                    text: qsTr("Available sensors:")
                }

                ListView {
                    id: series_list_view
                    height: 180
		    width: 150
                    Layout.fillWidth: true
                    
                    clip: true
                    
                    model: sensorModel2
                    delegate: CheckBox {
                        checked : false;
                        text: name
                        onClicked: {
                            selected = checked;
                        }
                    }
                }

                RowLayout {
                    id: rowLayout1
                    Layout.fillWidth: true
		    
                    Label {
                        id: spin_label1
                        text: qsTr("Nog iets")
                    }

                }
                
            }
        }
    }
}
