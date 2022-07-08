import sys
import os
import pandas as pd
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QInputDialog, QFileDialog, QMessageBox, QButtonGroup, QTableWidgetItem
from design import Ui_MainWindow
import whatsArcCore as wa

choice = None
message = None
mediaPath = None
productKey = None
csvPath = None
filteredCsvFileName = None


# Filter whatsapp contacts
class ExcelCheck(QtCore.QThread):
    updated = QtCore.pyqtSignal([int],[int,str])
    running = False

    def __init__(self, parent=None):
        super(ExcelCheck, self).__init__(parent)
        self.progPercent = 0

    def run(self):
        global csvPath,filteredCsvFileName
        contactNumber = wa.contactNumber
        contactName = wa.contactName

        if csvPath is not None:
            print("Web Page Open")
            print("SCAN YOUR QR CODE FOR WHATSAPP WEB")
            wa.whatsappLogin()
            
            head, tail = os.path.split(r""+csvPath)
            name = []
            mobile = []
            if len(contactNumber) > 0:
                # Iterate through the contacts
                for x in range(0, len(contactNumber)):
                    if wa.filterWhatsappNumbers(contactNumber[x]):
                        print(contactName[x]+" have whatsapp")
                        name.append(contactName[x])
                        mobile.append(contactNumber[x])
                    else:
                        print(contactName[x]+" does not have whatsapp")

                    self.progPercent = x/len(contactNumber)*100
                    self.updated[int].emit(int(self.progPercent))
                self.updated[int,str].emit(int(100),str("filter"))

                dict = {'name': name, 'mobile': mobile,'VAR1':None,'VAR2':None,'VAR3':None,'VAR4':None,'VAR5':None}
                df = wa.pd.DataFrame(dict)

                filteredCsvFileName = 'whatsapp_'+tail 
                
                df.to_csv(head+'/whatsapp_'+tail,index=False)


class Worker(QtCore.QThread):
    updated = QtCore.pyqtSignal([int],[int,str])
    running = False

    def __init__(self, interval=5, singleInterval=0, localInterval=5, parent=None):
        super(Worker, self).__init__(parent)
        self.progPercent = 0
        self.interval = interval
        self.singleInterval = singleInterval
        self.localInterval = localInterval

    def run(self):
        global csvPath
        contactNumber = wa.contactNumber
        
        rotateCounter = wa.rotateInterval
        
        if len(contactNumber) > 0:
            for i, number in enumerate(contactNumber):
                if wa.isRotate:
                    if rotateCounter == 0:
                        rotateCounter = wa.rotateInterval
                        try:
                            wa.quitBrowser()
                            wa.getNextAccount()
                            wa.whatsappLogin()
                        except:
                            pass

                wa.time.sleep(self.singleInterval)

                if self.localInterval == 0:
                    self.localInterval = 5
                    wa.time.sleep(self.interval)

                retry = True
                while retry is True:
                    try:
                        wa.sender(i,number)
                        retry = False
                    except Exception as e:
                        print(e)
                        wa.time.sleep(30)
                        # print("exception"+str(e))
                        wa.failed.append("{0} - {1}".format(wa.contactName[i],number))

                self.localInterval = self.localInterval - 1
                rotateCounter = rotateCounter - 1
            
                self.progPercent = i/len(contactNumber)*100
                self.updated[int].emit(int(self.progPercent))
            
            wa.logFile.close()
            self.updated[int,str].emit(int(100),str("sender"))

class Main(QtWidgets.QMainWindow):

    def __init__(self,parent=None):
        super(Main, self).__init__(parent=parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.btn_active = False

        self.ui.csvBrowse.clicked.connect(self.open_csv_dialog)
        self.ui.mediaBrowse.clicked.connect(self.open_media_dialog)
        # self.ui.messageWithMedia.toggled.connect(self.send_message_with_media)
        self.ui.runScript.clicked.connect(self.execute_script)
        self.ui.hasLink.clicked.connect(self.onHasLinkClicked)
        self.ui.isRotateCB.clicked.connect(self.onisRotateCBClicked)

        self.modeGroup = QButtonGroup()
        self.modeGroup.addButton(self.ui.onlyMessage)
        self.modeGroup.addButton(self.ui.onlyMedia)
        self.modeGroup.addButton(self.ui.messageWithMedia)
        self.modeGroup.addButton(self.ui.attachDocument)

        self.ui.onlyMedia.toggled.connect(self.onClickedMode)
        self.ui.onlyMessage.toggled.connect(self.onClickedMode)
        self.ui.attachDocument.toggled.connect(self.onClickedMode)
        self.ui.messageWithMedia.toggled.connect(self.onClickedMode)
        self.ui.actionDownload_Sample_CSV.triggered.connect(self.saveFileDialog)
        self.ui.addAccount.triggered.connect(self.showAddAccountDialog)
        self.ui.selectAccount.currentIndexChanged.connect(self.accountSelectionChanged)
        self.ui.deleteAccount.clicked.connect(self.accountDeleteConfirmation)

        self.ui.filterCsv.clicked.connect(self.initialiseWaFilter)

        self.setComboBox()
        self.fetchUpdatedAPI()

            
    def accountSelectionChanged(self,i):
        wa.account = self.ui.selectAccount.currentText()

    def open_csv_dialog(self):
        global csvPath
        filter = "Csv(*.csv)"
        csvFile = QFileDialog.getOpenFileName(None,"Select CSV", wa.fileSelectorPath,filter,"")
        csvPath = csvFile[0]
        # try:
        if csvPath != '':
            data = pd.read_csv(csvPath).fillna("")
            print(data)

        self.ui.tableWidget.setRowCount(data.shape[0]) 

        # Column count
        self.ui.tableWidget.setColumnCount(data.shape[1]+1)
        cdx = 0
        for index, row in data.iterrows():
            self.ui.tableWidget.setItem(index,cdx, QTableWidgetItem(''))
            self.ui.tableWidget.setItem(index,cdx+1, QTableWidgetItem(str(row['name'])))
            self.ui.tableWidget.setItem(index,cdx+2, QTableWidgetItem(str(row['mobile'])))
            self.ui.tableWidget.setItem(index,cdx+3, QTableWidgetItem(str(row['VAR1'])))
            self.ui.tableWidget.setItem(index,cdx+4, QTableWidgetItem(str(row['VAR2'])))
            self.ui.tableWidget.setItem(index,cdx+5, QTableWidgetItem(str(row['VAR3'])))
            self.ui.tableWidget.setItem(index,cdx+6, QTableWidgetItem(str(row['VAR4'])))
            self.ui.tableWidget.setItem(index,cdx+7, QTableWidgetItem(str(row['VAR5'])))
        # except:
        #     self.show_error_dialog("Select Valid CSV File")
        #     self.ui.csvInput.setText("")

    def open_media_dialog(self):
        global mediaPath,choice
        if choice == "document":
            filter = "All Files(*.*)"
        else:
            filter = "Custom Files(*.tiff *.pjp *.pjpeg *.jfif *.tif *.gif *.svg *.bmp *.png *.jpeg *.svgz *.jpg *.webp *.ico *.xbm *.dib *.m4v *.mp4 *.3gpp *.mov)"
        mediaFile = QFileDialog.getOpenFileName(None, "Select Media", wa.fileSelectorPath, filter)
        mediaPath = mediaFile[0]
        self.ui.mediaInput.setText(mediaPath)
       
    def saveFileDialog(self):
        options = QFileDialog.Options()
        rawFileName, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","Comma delimited (*.csv)", options=options)
        if rawFileName:
            print(rawFileName)
            filename, file_extension = os.path.splitext(rawFileName)
            wa.shutil.copy2('example.csv',filename+'.csv')

    def onClickedMode(self):
        global choice
        radioBtn = self.sender()
        if radioBtn.isChecked():
            if radioBtn.text() == "Only Message":
                choice = "onlyMessage"
                self.mediaController(True)
                self.textController(False)
                self.hasLinkController(False)
            elif radioBtn.text() == "Only Media":
                choice = "onlyMedia"
                self.mediaController(False)
                self.textController(True)
                self.hyperlinkController(True)
                self.hasLinkController(True)
            elif radioBtn.text() == "Document":
                choice = "document"
                self.mediaController(False)
                self.textController(True)
                self.hyperlinkController(True)
                self.hasLinkController(True)
            elif radioBtn.text() == "Message with Media":
                choice = "messageWithMedia"
                self.mediaController(False)
                self.textController(False)
                self.hyperlinkController(True)
                self.hasLinkController(True)
    
    def onHasLinkClicked(self):
        if self.ui.hasLink.isChecked():
            self.hyperlinkController(False)
        else:
            self.hyperlinkController(True)

    def onisRotateCBClicked(self):
        if self.ui.isRotateCB.isChecked():
            self.rotateAccountController(False)
        else:
            self.rotateAccountController(True)

    def rotateAccountController(self,args):
        self.ui.rotateAccSpin.setDisabled(args)
        self.ui.rotateAccLabel.setDisabled(args)
        self.ui.selectAccount.setDisabled(not args)

    def mediaController(self,args):
        self.ui.mediaBrowse.setDisabled(args)
        self.ui.mediaInput.setDisabled(args)

    def textController(self,args):
        self.ui.messageInput.setDisabled(args)

    def hyperlinkController(self,args):
        self.ui.hyperlinkInput.setDisabled(args)

    def hasLinkController(self,args):
        self.ui.hasLink.setDisabled(args)

    def execute_script(self):
        global message,choice,mediaPath
        self.ui.statusLabel.setText("Clearing Cache: ")
        wa.success = []
        wa.failed = []
        self.ui.statusLabel.setText("Sending messages: ")
        interval = self.ui.intervalSpin.value()
        singleInterval = self.ui.singleInterval.value()
        self.worker = Worker(interval=interval,singleInterval=singleInterval)
        wa.choice = choice

        if self.ui.isRotateCB.isChecked():
            wa.isRotate = True
            wa.rotateInterval = self.ui.rotateAccSpin.value()
        else:
            wa.isRotate = False

        if choice == "onlyMessage":
            wa.message = self.ui.messageInput.toPlainText()
            
            if self.ui.hasLink.isChecked():
                wa.hyperlink = self.ui.hyperlinkInput.text()
            else:
                wa.hyperlink = None

        elif choice == "onlyMedia":
            wa.encodeMedia(mediaPath)

        elif choice == "document":
            wa.encodeMedia(mediaPath)

        elif choice == "messageWithMedia":
            wa.message = self.ui.messageInput.toPlainText()
            wa.encodeMedia(mediaPath)
        
        wa.initialiseLogFile()
        self.parseTableData()
        print("Web Page Open")
    
        print("SCAN YOUR QR CODE FOR WHATSAPP WEB")
        wa.whatsappLogin()
        
        self.worker.updated[int].connect(self.updateValue)
        self.worker.updated[int,str].connect(self.updateValue)
        self.worker.start()
        
        # if wa.checkMessageStatus():
        #     self.showBrowserExitMessage()
        # else:
        #     self.show_information_dialog("Please Check message status before closing browser")

    def show_error_dialog(self, errorMessage):
        msg = QMessageBox()
        msg.setWindowTitle("Error")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(errorMessage)
        msg.exec_()

    def show_information_dialog(self, errorMessage):
        msg = QMessageBox()
        msg.setWindowTitle("Information")
        msg.setIcon(QMessageBox.Information)
        msg.setText(errorMessage)
        msg.exec_()

    def showAddAccountDialog(self):
        key, ok = QInputDialog.getText(self, 'Add Account', 'Enter account name:')

        if ok:
            if key in wa.accounts:
                self.show_error_dialog("Account name "+key+" already exists.Please choose another name")
                self.showAddAccountDialog()
            else:
                wa.account = key
                wa.whatsappLogin()
                self.setComboBox()

    def showBrowserExitMessage(self,sleep=5):
        wa.time.sleep(sleep)
        # wa.browser.minimize_window()
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("Do you want to quit the browser?")
        msgBox.setWindowTitle("Quit Browser")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        returnValue = msgBox.exec()
        if returnValue == QMessageBox.Ok:
            try:
                wa.browser.close()
                wa.browser.quit()
            except:
                pass 
        elif returnValue == QMessageBox.Cancel:
            pass
        
    def accountDeleteConfirmation(self):
        # wa.time.sleep(5)
        # wa.browser.minimize_window()
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("Are you sure want to delete account "+wa.account+"?")
        msgBox.setWindowTitle("Delete Account")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        returnValue = msgBox.exec()
        if returnValue == QMessageBox.Ok:
            if(wa.deleteAccount()):
                self.show_information_dialog("Account Deleted Successfully")
                self.setComboBox()
            else:
                self.show_error_dialog("Error deleting account")
        elif returnValue == QMessageBox.Cancel:
            pass

    def setComboBox(self):
        wa.getAccounts()
        self.ui.selectAccount.clear()
        for acc in wa.accounts:
            self.ui.selectAccount.addItem(acc)

    def initialiseWaFilter(self):
        self.parseTableData()
        self.ui.statusLabel.setText("Filtering whatsapp numbers: ")
        self.ui.filterCsv.setEnabled(False)
        self.btn_active = True
        self.tmr = ExcelCheck(self)
        self.tmr.updated[int].connect(self.updateValue)
        self.tmr.updated[int,str].connect(self.updateValue)
        self.tmr.start()

    def updateValue(self, data, mode=None):
        global filteredCsvFileName
        self.ui.progressBar.setValue(data)

        if filteredCsvFileName is None:
            filteredCsvFileName = "whatsapp_temp.csv"
        if data == 100:
            if mode == "filter":
                self.show_information_dialog("Whatsapp numbers extracted succefully and saved to your csv path as "+filteredCsvFileName)            
                self.showBrowserExitMessage(sleep=0)
            if mode == "sender":
                if wa.checkMessageStatus():
                    self.showBrowserExitMessage()
                else:
                    self.show_information_dialog("Please Check message status before closing browser")

            self.ui.statusLabel.setText("Status: ")
            self.ui.progressBar.setValue(0)
            self.ui.filterCsv.setEnabled(True)
            
            print("====================================")
            print("Task Completed")
            print("Success {}, to: {}".format(len(wa.success), wa.success))
            print("====================================")
            wa.failed = [x for x in wa.failed if x not in wa.success]
            print("Failed {}, to: {}".format(len(wa.failed), wa.failed))

    def fetchUpdatedAPI(self):
        print("fetchAPI function called")
        msg = QMessageBox()
        msg.setWindowTitle("Information")
        msg.setIcon(QMessageBox.Information)
        msg.setText("Error retrieving whatsapp API. Please check your internet or firewall settings.")
        msg.setStandardButtons(QMessageBox.Retry)
        while not wa.waitForInternetConnection():
            msg.exec_()
        # msg.close()

    def parseTableData(self):
        rows = self.ui.tableWidget.rowCount()
        columns = self.ui.tableWidget.columnCount()
        columnList = ['status','name', 'mobile', 'VAR1', 'VAR2', 'VAR3', 'VAR4', 'VAR5']

        data = pd.DataFrame(columns=['status','name', 'mobile', 'VAR1', 'VAR2', 'VAR3', 'VAR4', 'VAR5']) 

        for i in range(rows):
            for j in range(columns):
                data.loc[i, columnList[j]] = self.ui.tableWidget.item(i, j).text()
        
        # Clear lists
        wa.contactName = wa.contactNumber = wa.variables = []
        
        wa.contactName = data.name.tolist()
        # contactName.pop(0)
        wa.contactNumber = data.mobile.tolist()
        # contactNumber.pop(0)
        wa.variables.append(data.VAR1.tolist())
        wa.variables.append(data.VAR2.tolist())
        wa.variables.append(data.VAR3.tolist())
        wa.variables.append(data.VAR4.tolist())
        wa.variables.append(data.VAR5.tolist())


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())
