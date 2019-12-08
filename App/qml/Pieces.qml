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
                id: mplPieces
                objectName : "pieces"
                            
                Layout.fillWidth: true
                Layout.fillHeight: true
                
                Layout.minimumWidth: 10
                Layout.minimumHeight: 10
            }
            

	    // En er iets onder
	    Text {
		width: 400
                Layout.minimumHeight: 50
		text: 'Pieces links onder'
	    }

	}

      Connections {
            target: sensorModel
            onDataChanged: {
                draw_mpl.update_figure()
            }
      }

        Pane {
            id: right
            Layout.alignment: Qt.AlignLeft | Qt.AlignTop
            Layout.fillHeight: true
	    
            ColumnLayout {
                id: right_vbox
                spacing: 5
                
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
                    
                    model: sensorModel
                    delegate: CheckBox {
                        checked : false;
                        text: name
                        onClicked: {
                            selected = checked;
                        }
                    }
                }

                Label {
                    id: piecelabel
                    text: qsTr("Select pieces")
                }


		Button {
		    text: "New piece"
		    onClicked: draw_mpl.new_piece()
		}

                ListView {
                    id: create_pieces_view
                    height: 180
		    width: 150
                    Layout.fillWidth: true
                    
                    clip: true
                    
                    model: makePiecesModel
                    delegate: RowLayout {
			TextField {
			    placeholderText: qsTr("PieceName")
			}
			Text {
			    text: 'begin'
			}
			Text {
			    text: 'end'
			}

		    }

                }
		
            }
        }
    }
}
