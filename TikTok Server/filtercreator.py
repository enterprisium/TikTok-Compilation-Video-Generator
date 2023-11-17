from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5 import QtWidgets
from PyQt5.QtCore import *
from PyQt5 import QtGui
import scriptwrapper
from PyQt5.QtMultimedia import QMediaPlayer, QMediaPlaylist, QMediaContent
from PyQt5.QtCore import QDir, Qt, QUrl, pyqtSignal, QPoint, QRect, QObject
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer, QVideoFrame, QAbstractVideoSurface, QAbstractVideoBuffer, QVideoSurfaceFormat
from PyQt5.QtWidgets import *
import database
import os

current_path = os.path.dirname(os.path.realpath(__file__))

class Filter():
    def __init__(self, searchType, inputText, likeCount, shareCount, playCount, commentCount):

        # trending author hashtags
        self.searchType = searchType

        # string or list
        self.inputText = inputText

        self.likeCount = likeCount
        self.shareCount = shareCount
        self.playCount = playCount
        self.commentCount = commentCount



class FilterCreationWindow(QMainWindow):
    # update_log_found_clips = pyqtSignal(str, int, str)



    def __init__(self, window):
        QtWidgets.QWidget.__init__(self)
        uic.loadUi(f"{current_path}/UI/clipTemplateHandler.ui", self)
        self.window = window
        self.likeFilter.stateChanged.connect(self.updateDisplay)
        self.shareFilter.stateChanged.connect(self.updateDisplay)
        self.amountFilter.stateChanged.connect(self.updateDisplay)
        self.commentFilter.stateChanged.connect(self.updateDisplay)
        self.createFilter.clicked.connect(self.attemptCreateFilter)
        self.category.currentTextChanged.connect(self.changeCategory)

        self.changeCategory()

        self.savedFilters = database.getFilterNames()


    def changeCategory(self):
        isTrending = self.category.currentText() == "Trending"
        isHashTag = self.category.currentText() == "Hashtag"
        isAuthor = self.category.currentText() == "Author"


        self.inputText.show()

        if isTrending:
            self.inputText.hide()
            self.inputTextLabel.setText("")

        if isHashTag:
            self.inputTextLabel.setText("Enter comma separated Hashtags (no #) e.g. memes, lol, funny")

        if isAuthor:
            self.inputTextLabel.setText("Enter comma separated author names  e.g. charlidamelio, addisonre")


    def updateDisplay(self):

        useLikeFilter = bool(self.likeFilter.isChecked())
        useShareFilter = bool(self.shareFilter.isChecked())
        useAmountFilter = bool(self.amountFilter.isChecked())
        useCommentFilter = bool(self.commentFilter.isChecked())

        self.likeAmount.setEnabled(useLikeFilter)
        self.shareAmount.setEnabled(useShareFilter)
        self.playAmount.setEnabled(useAmountFilter)
        self.commentAmount.setEnabled(useCommentFilter)

    def attemptCreateFilter(self):

        useLikeFilter = bool(self.likeFilter.isChecked())
        useShareFilter = bool(self.shareFilter.isChecked())
        useAmountFilter = bool(self.amountFilter.isChecked())
        useCommentFilter = bool(self.commentFilter.isChecked())

        isTrending = self.category.currentText() == "Trending"
        isHashTag = self.category.currentText() == "Hashtag"
        isAuthor = self.category.currentText() == "Author"

        filterType = self.category.currentText()
        inputText = None

        likeAmount = None
        shareAmount = None
        playAmount = None
        commentAmount = None

        try:
            if useLikeFilter:
                likeAmount = int(self.likeAmount.text())
            if useShareFilter:
                shareAmount = int(self.shareAmount.text())
            if useAmountFilter:
                playAmount = int(self.playAmount.text())
            if useCommentFilter:
                commentAmount = int(self.commentAmount.text())
        except Exception:
            QMessageBox.information(self, 'Could not create filter!', "Make sure that the filter inputs are all numbers!", QMessageBox.Ok)
            return

        if isHashTag or isAuthor:
            if self.inputText.text() == "" or self.inputText.text().replace(" ", "") == "":
                QMessageBox.information(
                    self,
                    f'{filterType} type specified but no input text!',
                    "Enter a value into the input box! Add commas if you want multiple!",
                    QMessageBox.Ok,
                )
                return
            else:
                inputText = self.inputText.text().replace(" ", "")
                inputText = inputText.split(",")

        filterName = self.filterName.text()

        if filterName == "" or filterName.replace(" ", "") == "":
            QMessageBox.information(self, 'Please enter a filter name!', "Filter name needed!", QMessageBox.Ok)
            return

        if filterName in self.savedFilters:
            QMessageBox.information(
                self,
                'Filter already exists with name!',
                f"Please use a different name for this filter! This name ({filterName}) is already registered.",
                QMessageBox.Ok,
            )
            return

        filter = Filter(filterType, inputText, likeAmount, shareAmount, playAmount, commentAmount)
        database.addFilter(filterName, filter)
        self.window.update_combo_box_filter.emit()
        self.close()










