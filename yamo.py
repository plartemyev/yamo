#!/usr/bin/env python3

import sys
import media_recollect
from PyQt5 import QtWidgets, uic
from ui_resources import music_sort

# Ui_MainWindow, QtBaseClass = uic.loadUiType('ui_resources/music_sort.ui')


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = music_sort.Ui_MainWindow()
        # self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.initUI()

    def initUI(self):
        self.ui.sourceDirSelector.clicked.connect(self.dirSelectionDialog)
        self.ui.targetDirSelector.clicked.connect(self.dirSelectionDialog)
        self.show()

    def dirSelectionDialog(self):
        _dir = QtWidgets.QFileDialog.getExistingDirectory(directory='.')
        if self.sender().objectName() == 'sourceDirSelector':
            self.ui.sourceDirectoryInput.setText(_dir)
        elif self.sender().objectName() == 'targetDirSelector':
            self.ui.targetDirectoryInput.setText(_dir)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    yamo_ui = MainWindow()
    sys.exit(app.exec_())
