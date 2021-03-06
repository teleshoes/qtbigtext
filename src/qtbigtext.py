#!/usr/bin/python
#qtbigtext
#Copyright 2012 Elliot Wolk
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from dbus.mainloop.glib import DBusGMainLoop
import dbus
import dbus.service
import os
import re
import sys
import fcntl
import signal
import threading

signal.signal(signal.SIGINT, signal.SIG_DFL)

CONF = os.getenv("HOME") + '/.config/qtbigtext.conf'
DEFAULT_CONFIG = {
  'lineSeparator': 'false',
  'bgColor': 'black',
  'fgColor': 'white',
  'textFile': os.getenv("HOME") + '/MyDocs/qtbigtext.txt',
  'wordWrap': 'true',
  'typeface': 'Inconsolata',
  'minFontPt': '4',
  'maxFontPt': '600',
  'rotate': 'false',
  'fullScreen': 'true',
  'forceWidth': '',
  'forceHeight': '',
  'align': 'left',
}

class LineType:
  normal = 1
  separator = 2

sampleText = ("The quick brown fox jumped over the lazy dog.")

name = sys.argv[0]
usage = ("Usage:\n"
  + "  [OPTS]" + name + " TEXT [TEXT .. TEXT]  show 'TEXT TEXT ..'\n"
  + "  " + name + " -h  show this message\n"
  + "\n"
  + "  OPTS are --KEY=VAL {VAL can be empty}, and override config file:\n"
  + "    " + CONF + "\n"
  + "  default values are as follows:\n"
  + '\n'.join("    --"+k+"="+v for k, v in sorted(DEFAULT_CONFIG.items()))
)

def printErr(msg):
  sys.stderr.write(msg + "\n")

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
    config = Config()
    config.read()
    args = sys.argv[1:]
    while len(args) > 0 and args[0].startswith('--'):
      arg = args.pop(0)
      arg = re.sub("^--", "", arg)
      config.update(arg)

    conf = config.get()

    if len(args) > 0:
      s = ' '.join(args)
    else:
      s = readStdin()
    s = s.replace("\t", "    ")

    if s == "":
      s = readFile(conf['textFile'])
    if s == "":
      s = sampleText

    app = QApplication([])
    app.setStyleSheet("QWidget { background-color : %s; color : %s;}" % (
      conf['bgColor'], conf['fgColor']))

    if conf['rotate'].lower() == 'true':
      (w, h) = (conf['forceWidth'], conf['forceHeight'])
      conf['forceWidth'] = h
      conf['forceHeight'] = w

    qtBigText = QtBigText(conf)
    qtBigText.setText(s)

    if conf['rotate'].lower() == 'true':
      graphicsView = QGraphicsView()
      scene = QGraphicsScene(graphicsView)
      graphicsView.setScene(scene)

      proxy = QGraphicsProxyWidget()
      proxy.setWidget(qtBigText)
      proxy.setTransformOriginPoint(proxy.boundingRect().center())
      proxy.setRotation(90)
      scene.addItem(proxy)

      widget = graphicsView
    else:
      widget = qtBigText

    if conf['fullScreen'].lower() == "false":
      widget.show()
    else:
      widget.showFullScreen()

    DBusGMainLoop(set_as_default=True)
    QtBigTextDbusService(qtBigText)
    app.exec_()

class Config():
  def __init__(self):
    self.default()
  def default(self):
    self.conf = DEFAULT_CONFIG.copy()
  def get(self):
    return self.conf
  def read(self):
    try:
      with open(CONF, 'r') as f:
        for line in f:
          self.update(line)
    except IOError:
      self.default()
      self.write()
  def update(self, entry):
    m = re.search('\\s*([a-zA-Z]+)\\s*=\\s*(.*)', entry)
    if m != None:
      k = m.group(1)
      v = m.group(2)
      if k in self.conf:
        self.conf[k] = v
      else:
        printErr("Malformed or unknown option: " + k + "=" + v)
  def write(self):
    msg = ''
    for k,v in sorted(self.conf.items()):
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
    self.lock = threading.Lock()
  def getBusName(self):
    return dbus.service.BusName(
      'org.teleshoes.qtbigtext', bus=dbus.SessionBus())
  @dbus.service.method('org.teleshoes.qtbigtext')
  def test(self):
    pass
  @dbus.service.method('org.teleshoes.qtbigtext')
  def setText(self, text):
    self.lock.acquire()
    try:
      self.qtbigtext.setText(text)
    finally:
      self.lock.release()

class QtBigText(QWidget):
  def __init__(self, conf):
    QWidget.__init__(self)
    self.conf = conf
    self.layout = QVBoxLayout(self)
    self.labelCache = []
    self.frameCache = []
    self.fontCache = {}
    self.fontMetricCache = {}
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

    minPt = int(self.conf['minFontPt'])
    maxPt = int(self.conf['maxFontPt'])

    self.fontDecaPts = []
    decaPt = minPt*10
    while decaPt < maxPt*10:
      self.fontDecaPts.append(decaPt)
      decaPt += 1
    self.guessFontPtIndex = None
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
      [line, lineType] = row
      self.layout.addWidget(self.createLabel(line, font))
      if lineType == LineType.separator:
        self.layout.addWidget(self.createSeparator())
  def createLabel(self, text, font):
    if len(self.labelCache) == 0:
      label = QLabel()
      label.setWordWrap(False)
      style = self.getAlignStyle()
      if style != None:
        label.setStyleSheet(style)
      self.labelCache.append(label)
    label = self.labelCache.pop()
    label.setText(text)
    label.setFont(font)
    return label
  def getAlignStyle(self):
    align = self.conf['align'].lower()
    if align == 'left':
      return 'qproperty-alignment: AlignLeft;'
    elif align == 'center':
      return 'qproperty-alignment: AlignCenter;'
    elif align == 'right':
      return 'qproperty-alignment: AlignRight;'
    else:
      return None
  def createSeparator(self):
    if len(self.frameCache) == 0:
      sep = QFrame()
      sep.setFrameShape(QFrame.HLine)
      self.frameCache.append(sep)
    sep = self.frameCache.pop()
    return sep
  def clear(self):
    while self.layout.count() > 0:
      w = self.layout.takeAt(0).widget()
      w.setParent(None)
      if isinstance(w, QLabel):
        self.labelCache.append(w)
      elif isinstance(w, QFrame):
        self.frameCache.append(w)
  def screenWidth(self):
    return self.geometry.width()
  def screenHeight(self):
    return self.geometry.height()
  def calculateGrid(self, font):
    fm = self.constructFontMetrics(font)
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
    rows = []
    start = 0
    end = start + cols
    length = len(text)
    isWordWrap = self.conf['wordWrap'].lower() == "true"
    isLineSeparator = self.conf['lineSeparator'].lower() == "true"
    for i in range(length):
      c = text[i]
      lineBreak = False
      if c == "\n":
        end = i+1
        lineBreak = True
      elif isWordWrap and c == " ":
        end = i+1

      if i - start >= cols or lineBreak:
        line = text[start:end]
        rows.append(self.getRow(line, lineBreak, isLineSeparator))
        start = end
        end = start + cols

      if start+cols >= length:
        for line in text[start:].split("\n"):
          rows.append(self.getRow(line, True, isLineSeparator))
        break

    #remove empty trailing lines
    while len(rows) > 0 and rows[-1][0] == "":
      del rows[-1]

    #remove separator from last line
    if len(rows) > 0:
      rows[-1][1] = LineType.normal

    return rows
  def getRow(self, text, isLineBreak, isLineSeparator):
    if isLineBreak and isLineSeparator:
      lineType = LineType.separator
    else:
      lineType = LineType.normal
    text = text.replace('\n', '')
    return [text, lineType]
  def splitAt(self, s, n):
    for i in range(0, len(s), n):
      yield s[i:i+n]
  def textFits(self, text, font):
    return self.parseGrid(text, font) != None
  def constructFont(self, pointSize):
    if not pointSize in self.fontCache:
      font = QFont()
      font.setFamily(self.conf['typeface'])
      font.setPointSizeF(pointSize)
      font.setStyleStrategy(QFont.PreferAntialias)
      self.fontCache[pointSize] = font
    return self.fontCache[pointSize]
  def constructFontMetrics(self, font):
    p = font.pointSizeF()
    if not p in self.fontMetricCache:
      self.fontMetricCache[p] = QFontMetrics(font)
    return self.fontMetricCache[p]
  def testIndex(self, text, decaFontPtIndex):
    if decaFontPtIndex < 0:
      return True
    if decaFontPtIndex >= len(self.fontDecaPts):
      return False
    font = self.constructFont(self.fontDecaPts[decaFontPtIndex]/10)
    return self.textFits(text, font)
  def selectPointSize(self, text):
    minIndex = 0
    maxIndex = len(self.fontDecaPts)

    if self.guessFontPtIndex != None:
      midIndex = self.guessFontPtIndex

      #check guess index to see if its exactly correct
      if self.testIndex(text, midIndex):
        minIndex = midIndex
        if not self.testIndex(text, midIndex+1):
          maxIndex = midIndex
        midIndex = int((minIndex+maxIndex)/2)
    else:
      midIndex = int((minIndex+maxIndex)/2)

    while minIndex < midIndex:
      if self.testIndex(text, midIndex):
        minIndex = midIndex
      else:
        maxIndex = midIndex-1
      midIndex = int((minIndex + maxIndex) / 2)

    self.guessFontPtIndex = midIndex
    fontPt = self.fontDecaPts[midIndex]/10
    return fontPt

if __name__ == "__main__":
  sys.exit(main())
