#!/usr/bin/python
#qtbigtext
#Copyright 2012 Elliot Wolk
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from PySide.QtGui import *
from PySide.QtCore import *
from dbus.mainloop.glib import DBusGMainLoop
import dbus
import dbus.service
import os
import re
import sys
import fcntl
import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)

CONF = os.getenv("HOME") + '/.config/qtbigtext.conf'

sampleText = ("The quick brown fox jumped over the lazy dog.")

name = sys.argv[0]
usage = ("Usage:\n"
  + "  " + name + " TEXT [TEXT .. TEXT]  show 'TEXT TEXT ..'\n"
  + "  " + name + " -h  show this message\n"
)

def printErr(msg):
  sys.stderr.write(msg)

def readStdin():
  fd = sys.stdin.fileno()
  fl = fcntl.fcntl(fd, fcntl.F_GETFL)
  fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
  sBuf = ''
  while True:
    try:
      if sys.version_info[0] >= 3:
        s = os.read(fd, 512).decode('utf8')
      else:
        s = unicode(os.read(fd, 512), 'utf8')
    except:
      s = ''
    sBuf += s
    if s == "":
      break
  return sBuf

def readFile(path):
  try:
    with open(path) as f:
      return f.read()
  except IOError:
    return ''

def main():
  if len(sys.argv) == 2 and sys.argv[1] == '-h':
    print(usage)
    return 0
  else:
    if len(sys.argv) > 1:
      s = ' '.join(sys.argv[1:])
    else:
      s = readStdin()
    s = s.replace("\t", "    ")

    conf = Config().read()

    if s == "":
      s = readFile(conf['textFile'])
    if s == "":
      s = sampleText

    app = QApplication([])
    app.setStyleSheet("QWidget { background-color : %s; color : %s;}" % (
      conf['bgColor'], conf['fgColor']))

    qtBigText = QtBigText(conf)
    qtBigText.setText(s)
    qtBigText.showFullScreen()

    DBusGMainLoop(set_as_default=True)
    QtBigTextDbusService(qtBigText)
    app.exec_()

class Config():
  def default(self):
    return {
      'bgColor': 'black',
      'fgColor': 'white',
      'textFile': os.getenv("HOME") + '/MyDocs/qtbigtext.txt',
      'wordWrap': 'true',
      'typeface': 'Inconsolata',
      'minFontPt': '4',
      'maxFontPt': '600',
      'forceWidth': '',
      'forceHeight': ''}
  def read(self):
    conf = self.default()
    try:
      with open(CONF, 'r') as f:
        for line in f:
          m = re.search('\\s*([a-zA-Z]+)\\s*=\\s*(.*)', line)
          if m != None and m.group(1) in conf:
            conf[m.group(1)] = m.group(2)
    except IOError:
      self.write()
    return conf
  def write(self):
    conf = self.default()
    msg = ''
    for k,v in sorted(conf.items()):
      msg += k + '=' + v + "\n"
    try:
      with open(CONF, 'w') as f:
        f.write(msg)
    except IOError as e:
      printErr(e)

class QtBigTextDbusService(dbus.service.Object):
  def __init__(self, qtbigtext):
    dbus.service.Object.__init__(self, self.getBusName(), '/')
    self.qtbigtext = qtbigtext
  def getBusName(self):
    return dbus.service.BusName(
      'org.teleshoes.qtbigtext', bus=dbus.SessionBus())
  @dbus.service.method('org.teleshoes.qtbigtext')
  def setText(self, text):
    self.qtbigtext.setText(text)

class QtBigText(QWidget):
  def __init__(self, conf):
    QWidget.__init__(self)
    self.conf = conf
    self.layout = QVBoxLayout(self)
    self.geometry = QDesktopWidget().availableGeometry()
    if len(self.conf['forceWidth']) > 0:
      w = int(self.conf['forceWidth'])
      self.setFixedWidth(w)
      self.geometry.setWidth(w)
    if len(self.conf['forceHeight']) > 0:
      h = int(self.conf['forceHeight'])
      self.setFixedHeight(h)
      self.geometry.setHeight(h)
    self.setContentsMargins(0,0,0,0)
  def setText(self, text):
    self.clear()
    font = self.constructFont(self.selectPointSize(text))
    grid = self.parseGrid(text, font)

    if grid == None:
      printErr("text too big\n")
      text = "!"
      font = self.constructFont(self.selectPointSize(text))
      grid = self.parseGrid(text, font)
      if grid == None:
        printErr("failure: could not fit one character on screen\n")
        sys.exit(1)

    for row in grid:
      self.layout.addWidget(self.createLabel(row, font))
  def createLabel(self, text, font):
    label = QLabel(text)
    label.setWordWrap(False)
    label.setFont(font)
    return label
  def clear(self):
    while self.layout.count() > 0:
      w = self.layout.takeAt(0).widget()
      w.setParent(None)
      w.deleteLater()
  def screenWidth(self):
    return self.geometry.width()
  def screenHeight(self):
    return self.geometry.height()
  def calculateGrid(self, font):
    fm = QFontMetrics(font)
    w = fm.width('W')
    h = fm.height()
    rows = int(self.screenHeight() / h)
    cols = int(self.screenWidth() / w)
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
    isWordWrap = False
    if self.conf['wordWrap'].lower() == "true":
      isWordWrap = True
    for i in range(length):
      c = text[i]
      forceNew = False
      if c == "\n":
        end = i+1
        forceNew = True
      elif isWordWrap and c == " ":
        end = i+1

      if i - start >= cols or forceNew:
        lines.append(text[start:end])
        start = end
        end = start + cols

      if start+cols >= length:
        lines += text[start:].split("\n")
        break

    lines = [x.replace('\n', '') for x in lines]

    #remove empty trailing lines
    while len(lines) > 0 and lines[-1] == "":
      del lines[-1]

    return lines

  def splitAt(self, s, n):
    for i in range(0, len(s), n):
      yield s[i:i+n]
  def textFits(self, text, font):
    return self.parseGrid(text, font) != None
  def constructFont(self, pointSize):
    font = QFont(self.conf['typeface'], pointSize)
    font.setStyleStrategy(QFont.PreferAntialias)
    return font
  def selectPointSize(self, text):
    minPt = int(self.conf['minFontPt'])
    maxPt = int(self.conf['maxFontPt'])
    midPt = (minPt + maxPt) / 2
    while minPt < midPt:
      font = self.constructFont(midPt)
      if self.textFits(text, font):
        minPt = midPt
      else:
        maxPt = midPt-1
      midPt = (minPt + maxPt) / 2
    return midPt

if __name__ == "__main__":
  sys.exit(main())
