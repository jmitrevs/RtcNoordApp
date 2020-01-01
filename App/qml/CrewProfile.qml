import QtQuick 2.13
import QtQuick.Controls 2.13
import QtQuick.Layouts 1.12
import Backend 1.0

// Profile Crew report

Item {
    id: prcrew
    
    Text {
	text: 'Profile crew report'
    }

    ColumnLayout {
	Text {
	    text: 'boven'
	}

	// plots in the boat profile
        FigureToolbar {
            id: crewView
            objectName : "viewcrew"
                            
            Layout.fillWidth: true
            Layout.fillHeight: true
                
            Layout.minimumWidth: 1000
            Layout.minimumHeight: 400
        }
    }
}
