#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
import media_recollect as mr
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QDir

Ui_MainWindow, QtBaseClass = uic.loadUiType('music_sort.ui')
# import music_sort


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
        # self.ui = music_sort.Ui_MainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.initUI()

    def initUI(self):
        self.ui.sourceDirSelectBtn.clicked.connect(self.dirSelectionDialog)
        self.ui.targetDirSelectBtn.clicked.connect(self.dirSelectionDialog)
        self.ui.sourceDirectoryInput.editingFinished.connect(self.sourceDirProvided)
        self.ui.operationModeRbtnGroup.buttonClicked.connect(self.operationModeChanged)
        self.ui.commenceBtn.clicked.connect(self.commenceProcessing)
        self.ui.progressBar.hide()

        self.show()

    def dirSelectionDialog(self):
        if self.sender().objectName() == 'sourceDirSelectBtn':
            _dir = QDir.toNativeSeparators(
                QtWidgets.QFileDialog.getExistingDirectory(directory=self.ui.sourceDirectoryInput.text()))
            self.ui.sourceDirectoryInput.setText(_dir)
            self.sourceDirProvided()
        elif self.sender().objectName() == 'targetDirSelectBtn':
            _dir = QDir.toNativeSeparators(
                QtWidgets.QFileDialog.getExistingDirectory(directory=self.ui.targetDirectoryInput.text()))
            self.ui.targetDirectoryInput.setText(_dir)

    def sourceDirProvided(self):
        _source_dir = self.ui.sourceDirectoryInput.text()
        if os.path.isdir(_source_dir):
            if len(self.ui.targetDirectoryInput.text()) == 0:
                self.ui.targetDirectoryInput.setText(_source_dir)
            self.ui.commenceBtn.setEnabled(True)
            self.ui.commenceBtn.setEnabled(True)

    def operationModeChanged(self):  # Set log to warning
        _selected_mode = self.ui.operationModeRbtnGroup.checkedButton()
        _selected_loglevel = self.ui.loggingLevelRbtnGroup.checkedButton()

        if _selected_mode != self.ui.noopRbtn:
            if _selected_loglevel == self.ui.infoRbtn:
                self.ui.warningRbtn.setChecked(True)

        if _selected_mode == self.ui.noopRbtn and _selected_loglevel == self.ui.warningRbtn:
            self.ui.infoRbtn.setChecked(True)

    def commenceProcessing(self):
        self.ui.loggingOutputField.clear()

        _log_Level_selected = self.ui.loggingLevelRbtnGroup.checkedButton()
        if _log_Level_selected == self.ui.infoRbtn:
            logging.getLogger().setLevel(logging.INFO)
        elif _log_Level_selected == self.ui.debugRbtn:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.WARNING)

        params = {'source_dir': self.ui.sourceDirectoryInput.text(), 'target_dir': self.ui.targetDirectoryInput.text()}

        if self.ui.layoutAlbumsRbtn.isChecked():
            params['dir_structure'] = 'albums'
        else:
            params['dir_structure'] = 'plain'

        params['no_indexes'] = self.ui.noIndexesChkBtn.isChecked()
        # TODO: add option to process only 'original' compositions - omitting anything like 'SongName (instrumental)'

        op_mode_selected = self.ui.operationModeRbtnGroup.checkedButton().objectName()
        if op_mode_selected == 'copyRbtn':
            params['op_mode'] = 'copy'
        elif op_mode_selected == 'moveRbtn':
            params['op_mode'] = 'move'
        else:
            params['op_mode'] = 'no-op'
            
        if params['op_mode'] == 'copy' and params['source_dir'] == params['target_dir']:
            logging.warning('Attempted to re-organize files in-place using copy op_mode. That would be a mess.\n')
            self.ui.commenceBtn.setEnabled(False)
            self.ui.commenceBtn.setEnabled(True)
            return

        mp3_files = mr.scan_dir_for_media(params['source_dir'], [])

        self.ui.progressBar.setUpdatesEnabled(True)
        self.ui.progressBar.setMaximum(len(mp3_files))
        self.ui.progressBar.setValue(0)
        self.ui.progressBar.setEnabled(True)
        self.ui.progressBar.show()

        m_lib = mr.MediaLib(mp3_files)
        if self.ui.forcePerformerDirChkBtn.isChecked():
            m_lib.multiple_performers = True

        m_lib.straighten_performers_line()
        m_lib.check_multiple_performers_presence()

        for performer in m_lib.get_performers():
            for album in m_lib.get_albums(performer):
                for _track in mr.MediaAlbum.albums[performer][album].compositions:
                    m_lib.process_file(params, mr.MediaAlbum.albums[performer][album], _track)
                    self.ui.progressBar.setValue(self.ui.progressBar.value() + 1)

        mr.MediaAlbum.albums.clear()
        del mp3_files
        self.ui.commenceBtn.setEnabled(False)
        self.ui.commenceBtn.setEnabled(True)
        self.ui.progressBar.setUpdatesEnabled(False)
        self.ui.progressBar.setDisabled(True)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    yamo_ui = MainWindow()

    logging.captureWarnings(True)
    logWidget = QtLogFrame(yamo_ui.ui.loggingOutputField)
    log_message_format = '%(name)s:%(levelname)s %(message)s'
    logWidget.setFormatter(logging.Formatter(log_message_format, datefmt='%Y%m%d %H:%M:%S'))
    logging.getLogger().addHandler(logWidget)
    logging.getLogger().setLevel(logging.WARNING)

    sys.exit(app.exec_())
