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
            


	    /* En er iets onder
	    Text {
		width: 400
                Layout.minimumHeight: 50
		text: 'View piece links onder'
	    }
	    */
	}

	Connections {
            target: sensorModel3
            onDataChanged: {
                piece_mpl.update_figure()
            }
	}

	Connections {
            target: sensorModel4
            onDataChanged: {
                piece_mpl.update_figure()
            }
	}


        Pane {
            id: right
            Layout.alignment: Qt.AlignLeft | Qt.AlignTop
            Layout.fillHeight: true
	    
	    Row {
		ColumnLayout {
                    id: right_vbox
                    spacing: 2
                
                    Label {
			id: log_label
			text: draw_mpl.sessionName
                    }

                    ListView {
			id: series_list_view
			height: 180
			width: 150
			Layout.fillWidth: true
                    
			clip: true
                    
			model: sensorModel3
			delegate: CheckBox {
                            checked : selected;
			    font.pixelSize: 12
                            text: name
                            onClicked: {
				selected = checked;
                            }
			}
                    }

                    RowLayout {
			id: rowLayout1
			Layout.fillWidth: true
		    
			// items zijn piece namen
			ComboBox {
			    model: draw_mpl.the_pieces
			    onActivated: piece_mpl.set_piece(currentText)
			}
                    }
		}

		// The second session
		ColumnLayout {
                    id: right_vbox1
                    spacing: 2
                
		    Button {
			text: piece_mpl.sessionName

			onClicked: { seconddialog.open()
				   }
		    }

                    ListView {
			id: series_list_view2
			height: 180
			width: 150
			Layout.fillWidth: true
                    
			clip: true
                    
			model: sensorModel4
			delegate: CheckBox {
                            checked : selected;
			    font.pixelSize: 12
                            text: name
                            onClicked: {
				selected = checked;
                            }
			}
                    }

                    RowLayout {
			id: rowLayout2
			Layout.fillWidth: true
		    
			ComboBox {
			    model: piece_mpl.the_2nd_pieces
			    onActivated: piece_mpl.set_2nd_piece(currentText)
			}
                    }
		}




	    }
	}
    }
}
