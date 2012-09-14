#!/usr/bin/python
#qtbigtext
#Copyright 2012 Elliot Wolk
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from PySide.QtGui import *

import os
import sys
import fcntl
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

def readStdin():
  fd = sys.stdin.fileno()
  fl = fcntl.fcntl(fd, fcntl.F_GETFL)
  fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
  sBuf = ''
  while True:
    try:
      s = os.read(fd, 512)
    except:
      s = ''
    sBuf += s
    if s == "":
      break
  return sBuf

def main():
  if len(sys.argv) == 2 and sys.argv[1] == '-h':
    print usage
    return 0
  else:
    if len(sys.argv) > 1:
      s = ' '.join(sys.argv[1:])
    else:
      s = readStdin()
    s = s.replace("\t", "    ")

    if s == "":
      s = sampleText
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
    self.geometry = QDesktopWidget().availableGeometry()
    self.setContentsMargins(0,0,0,0)
  def setText(self, text):
    self.clear()
    font = self.constructFont(self.selectPointSize(text))
    for row in self.parseGrid(text, font):
      rowLabel = QLabel(row)
      rowLabel.setWordWrap(False)
      rowLabel.setFont(font)
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
  def parseGrid(self, text, font):
    rows, cols = self.calculateGrid(font)
    if len(text) > (rows * cols):
      return None
    else:
      grid = self.wordWrap(text, cols)
      if len(grid) > rows:
        return None
      else:
        return grid
  def wordWrap(self, text, cols):
    lines = []
    start = 0
    end = start + cols
    length = len(text)
    for i in range(0, length):
      if start+cols >= length:
        lines += text[start:].split("\n")
        break

      c = text[i]
      forceNew = False
      if c == "\n":
        end = i+1
        forceNew = True
      elif c == " ":
        end = i+1

      if start + i >= cols or forceNew:
        lines.append(text[start:end])
        start = end
        end = start + cols

    lines = map (lambda x: x.replace('\n', ''), lines)

    #remove empty trailing lines
    while len(lines) > 0 and lines[-1] == "":
      del lines[-1]

    return lines

  def splitAt(self, s, n):
    for i in xrange(0, len(s), n):
      yield s[i:i+n]
  def textFits(self, text, font):
    return self.parseGrid(text, font) != None
  def constructFont(self, pointSize):
    font = QFont(TYPEFACE, pointSize)
    font.setStyleStrategy(QFont.PreferAntialias)
    return font
  def selectPointSize(self, text):
    minPt = MIN_FONT_PT
    maxPt = MAX_FONT_PT
    midPt = (minPt + maxPt) / 2
    print str(minPt) + " - " + str(maxPt)
    while minPt < midPt:
      font = self.constructFont(midPt)
      if self.textFits(text, font):
        minPt = midPt
      else:
        maxPt = midPt-1
      midPt = (minPt + maxPt) / 2
      print str(midPt)
    return midPt

if __name__ == "__main__":
  sys.exit(main())
