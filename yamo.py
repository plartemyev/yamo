#!/usr/bin/env python3

import sys
import os
import logging
from media_recollect import media_recollect as mr
from PyQt5 import QtWidgets, uic
from ui_resources import music_sort

# Ui_MainWindow, QtBaseClass = uic.loadUiType('ui_resources/music_sort.ui')


class QtLogFrame(logging.Handler):
    def __init__(self, parent_widget: QtWidgets.QPlainTextEdit):
        super().__init__()
        self.widget = parent_widget

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = music_sort.Ui_MainWindow()
        # self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.initUI()

    def initUI(self):
        self.ui.sourceDirSelectBtn.clicked.connect(self.dirSelectionDialog)
        self.ui.targetDirSelectBtn.clicked.connect(self.dirSelectionDialog)
        self.ui.sourceDirectoryInput.editingFinished.connect(self.sourceDirProvided)
        self.ui.commenceBtn.clicked.connect(self.commenceProcessing)
        self.ui.progressBar.hide()

        self.show()

    def dirSelectionDialog(self):
        _dir = QtWidgets.QFileDialog.getExistingDirectory(directory='.')
        if self.sender().objectName() == 'sourceDirSelectBtn':
            self.ui.sourceDirectoryInput.setText(_dir)
            self.sourceDirProvided()
        elif self.sender().objectName() == 'targetDirSelectBtn':
            self.ui.targetDirectoryInput.setText(_dir)

    def sourceDirProvided(self):
        _source_dir = self.ui.sourceDirectoryInput.text()
        if os.path.isdir(_source_dir):
            if len(self.ui.targetDirectoryInput.text()) == 0:
                self.ui.targetDirectoryInput.setText(_source_dir)
            self.ui.commenceBtn.setEnabled(True)

    def commenceProcessing(self):
        params = {'source_dir': self.ui.sourceDirectoryInput.text(), 'target_dir': self.ui.targetDirectoryInput.text()}

        if self.ui.layoutAlbumsRbtn.isChecked():
            params['dir_structure'] = 'albums'
        else:
            params['dir_structure'] = 'plain'

        op_mode_selected = self.ui.operationModeRbtnGroup.checkedButton().objectName()
        if op_mode_selected == 'copyRbtn':
            params['op_mode'] = 'copy'
        elif op_mode_selected == 'moveRbtn':
            params['op_mode'] = 'move'
        else:
            params['op_mode'] = 'no-op'

        mp3_files = mr.scan_dir_for_media(params['source_dir'], [])

        self.ui.progressBar.setMaximum(len(mp3_files))
        self.ui.progressBar.setValue(0)
        self.ui.progressBar.setEnabled(True)
        self.ui.progressBar.show()

        m_lib = mr.MediaLib(mp3_files)
        for performer in m_lib.get_performers():
            for album in m_lib.get_albums(performer):
                for _track in mr.MediaAlbum.albums[performer][album].compositions:
                    m_lib.process_file(params, mr.MediaAlbum.albums[performer][album], _track)
                    self.ui.progressBar.setValue(self.ui.progressBar.value() + 1)

        mr.MediaAlbum.albums = {}
        del mp3_files


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    yamo_ui = MainWindow()

    logging.captureWarnings(True)
    logWidget = QtLogFrame(yamo_ui.ui.loggingOutputField)
    log_message_format = '%(name)s:%(levelname)s %(message)s'
    logWidget.setFormatter(logging.Formatter(log_message_format, datefmt='%Y%m%d %H:%M:%S'))
    logging.getLogger().addHandler(logWidget)
    logging.getLogger().setLevel(logging.INFO)

    sys.exit(app.exec_())
