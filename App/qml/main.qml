import QtQuick 2.13
import QtQuick.Controls 2.13
import QtQuick.Layouts 1.12
import QtQuick.Dialogs 1.3

ApplicationWindow {
    id: applicationWindow
    visible: true
    width: 800
    height: 480
    title: qsTr("RTCNoord")


    MessageDialog {
        id: aboutDialog
        icon: StandardIcon.Information
        title: qsTr("About")
        text: "RTCNoord app"
        informativeText: qsTr("Verwerk Powerline data")
    }

    Action {
        id: copyAction
        text: qsTr("&Copy")
        shortcut: StandardKey.Copy

	//iconName: "edit-copy"
        enabled: (!!activeFocusItem && !!activeFocusItem["copy"])
        onTriggered: activeFocusItem.copy()
    }

    Action {
        id: cutAction
        text: qsTr("Cu&t")
        shortcut: StandardKey.Cut
        //iconName: "edit-cut"
        enabled: (!!activeFocusItem && !!activeFocusItem["cut"])
        onTriggered: activeFocusItem.cut()
    }

    Action {
        id: pasteAction
        text: qsTr("&Paste")
        shortcut: StandardKey.Paste
        //iconName: "edit-paste"
        enabled: (!!activeFocusItem && !!activeFocusItem["paste"])
        onTriggered: activeFocusItem.paste()
    }

    menuBar: MenuBar {
	contentHeight:20
        Menu {
            title: qsTr("&Session")
            MenuItem {
                text: qsTr("C&reate session")
                onTriggered: Qt.quit()
            }
            MenuItem {
                text: qsTr("S&elect session")
                onTriggered: Qt.quit()
            }
            MenuItem {
                text: qsTr("Clear caches")
                onTriggered: Qt.quit()
            }
        }
        Menu {
            title: qsTr("&Config")
            MenuItem {
                action: cutAction
            }
            MenuItem {
                action: copyAction
            }
            MenuItem {
                action: pasteAction
            }
        }
        Menu {
            title: qsTr("&Help")
            MenuItem {
                text: qsTr("About...")
                onTriggered: aboutDialog.open()
            }
        }

    }


    StackLayout {
    // SwipeView {
        id: swipeView
        width: parent.width
	height: parent.height
	
        anchors.horizontalCenter: parent.horizontalCenter
	
        currentIndex: tabBar.currentIndex
	
        Pieces {
            id: iets1
        }

        ViewPiece {
            id: iets2
        }

        SessionInfo {
            id: iets3
        }

        Profile {
            id: iets4
        }

        NogWat{
            id: iets5
        }
    }

    footer: TabBar {
        id: tabBar
        implicitWidth: 800
        currentIndex: swipeView.currentIndex


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

        TabButton {
            id: tabButton2
	    implicitHeight:20
            text: qsTr("Session info")
        }

        TabButton {
            id: tabButton3
	    implicitHeight:20
            text: qsTr("Profile")
        }

        TabButton {
            id: tabButton4
	    implicitHeight:20
            text: qsTr("Nog wat ..")
	}
    }
}

