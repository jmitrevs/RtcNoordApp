import QtQuick 2.13
import QtQuick.Controls 2.13
import QtQuick.Layouts 1.12

ApplicationWindow {
    id: applicationWindow
    visible: true
    width: 400
    height: 400
    
    StackLayout {
	id: stackLayout
	width: parent.width
	height: parent.height
	
	currentIndex: tabBar.currentIndex
	Pieces {
            id: iets1
	}
	ViewPiece {
            id: iets2
	}
    }

    footer: TabBar {
        id: tabBar
        currentIndex: stackLayout.currentIndex
        TabButton {
            id: tabButton
	    implicitHeight:20
            text: qsTr("Setup pieces")
        }
        TabButton {
            id: tabButton1
	    implicitHeight:20
            text: qsTr("View piece")
        }
    }
}

