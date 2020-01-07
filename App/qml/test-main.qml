import QtQuick 2.13
import QtQuick.Controls 2.13
import QtQuick.Layouts 1.12
import QtQuick.Dialogs 1.3

ApplicationWindow {
    id: applicationWindow
    visible: true
    width: 900
    height: 600
    title: qsTr("RTCNoord")

    FileDialog {
        id: filedialog
        nameFilters: ["CSV files (*.csv)", "All Files (*.*)"]
	folder: '/tmp'
	onAccepted: {
	    console.log("You chose: " + fileDialog.fileUrls)
            Qt.quit()
	}
    } 

    Text {
	text: "draw_mpl.statusText"
    }

}

