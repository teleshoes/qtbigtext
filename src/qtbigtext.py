#!/usr/bin/python
#qtbigtext
#Copyright 2012 Elliot Wolk
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from PySide.QtGui import *

import sys
import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)

TYPEFACE= "Inconsolata"
MIN_FONT_PT = 4
MAX_FONT_PT = 600

sampleText = ( ""
  + "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod "
  + "tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim "
  + "veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea "
  + "commodo consequat. Duis aute irure dolor in reprehenderit in voluptate "
  + "velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint "
  + "occaecat cupidatat non proident, sunt in culpa qui officia deserunt "
  + "mollit anim id est laborum."
  + " `~!@#$%^&*()_ +-=[]\\{}|;':\",./<>?"
  + " abcdefghijkl mnopqrstuvwxyz"
  + " ABCDEFGHIJKL MNOPQRSTUVWXYZ"
  + " 0123456789"
)

name = sys.argv[0]
usage = ("Usage:\n"
  + "  " + name + " TEXT [TEXT .. TEXT]  show 'TEXT TEXT ..'\n"
  + "  " + name + " -h  show this message\n"
)

def main():
  if len(sys.argv) == 2 and sys.argv[1] == '-h':
    print usage
    return 0
  else:
    if len(sys.argv) > 1:
      s = ' '.join(sys.argv[1:])
    else:
      s = sampleText
    s = s.replace("\n", " ")
    app = QApplication([])

    qtBigText = QtBigText()
    qtBigText.setText(s)
    
    widget = QWidget()
    widget.setLayout(qtBigText)
    widget.showFullScreen()
    app.exec_()

class QtBigText(QVBoxLayout):
  def __init__(self):
    QVBoxLayout.__init__(self)
    self.geometry = QDesktopWidget().screenGeometry()
  def setText(self, text):
    self.clear()
    self.font = self.selectFont(text)
    for row in self.getRows(text):
      rowLabel = QLabel(row)
      rowLabel.setWordWrap(False)
      rowLabel.setFont(self.font)
      self.addWidget(rowLabel)
  def clear(self):
    while self.count() > 0:
      self.takeAt(0).deleteLater()
  def screenWidth(self):
    return self.geometry.width()
  def screenHeight(self):
    return self.geometry.height()
  def calculateGrid(self, font):
    fm = QFontMetrics(font)
    w = fm.width('W')
    h = fm.height()
    rows = self.screenHeight() / h
    cols = self.screenWidth() / w
    return (rows, cols)
  def getRows(self, s):
    #TODO implement word wrap here
    rows, cols = self.calculateGrid(self.font)
    for x in xrange(0, len(s), cols):
      yield s[x:x+cols]
  def textFits(self, text, rows, cols):
    #TODO implement word wrap here
    return len(text) <= rows * cols
  def selectFont(self, text):
    minPt = MIN_FONT_PT
    maxPt = MAX_FONT_PT
    print str(minPt) + " - " + str(maxPt)
    while minPt < maxPt - 1:
      mid = (minPt + maxPt) / 2
      rows, cols = self.calculateGrid(QFont(TYPEFACE, mid))
      if self.textFits(text, rows, cols):
        minPt = mid
      else:
        maxPt = mid-1
      print str(minPt) + " - " + str(maxPt)
    font = QFont(TYPEFACE, maxPt)
    font.setStyleStrategy(QFont.PreferAntialias)
    return font

if __name__ == "__main__":
  sys.exit(main())
