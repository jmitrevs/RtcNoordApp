import QtQuick 2.13
import QtQuick.Controls 2.13
import QtQuick.Layouts 1.12
import Backend 1.0

// Profile Boat report

Item {
    id: prboat

    ColumnLayout {
	Text {
	    text: 'boven'
	}

	Row {
	    spacing:10
    
	    TableView {
		id: boatTableView
		columnWidthProvider: function (column) { return column == 0 ? 150 : 50; }
		rowHeightProvider: function (column) { return 20; }
		model: boatTableModel
		height: 200
		width: 400  // dit moet anders...
		delegate: Rectangle {
		    // implicitWidth: 100
		    height: 50
		    color: {(index%boatTableView.rows)%2 ? 'gainsboro' : 'antiquewhite'}
		    //  tableView rows en columns gebruiken: om en om andere kleuren
		    Text {
			text: display
		    }
		}
		ScrollIndicator.horizontal: ScrollIndicator { }
		ScrollIndicator.vertical: ScrollIndicator { }
	    }
	    Button {
		text: 'Create profile'
		onPressed: {
		    prof_1.make_profile();
		    boatTableView.forceLayout()
		}
	    }
	}
	Text {
	    text: 'beneden'
	}

	// plots in the boat profile
        FigureToolbar {
            id: boatView
            objectName : "viewboat"
                            
            Layout.fillWidth: true
            Layout.fillHeight: true
                
            Layout.minimumWidth: 1000
            Layout.minimumHeight: 400
        }

    }
}
