# -*- coding: utf-8 -*-
"""
Created on Sun Jul 16 01:12:32 2017

@author: marzipan
"""
import sys
from PySide.QtCore import *
from PySide.QtGui import * 

try:
    app = QApplication(sys.argv)
except RuntimeError:
    pass
window = QWidget()
window.setGeometry(0, 0, 500, 300)
window.setWindowTitle("PyQT Tuts!")
lay = QGridLayout()
window.setLayout(lay)
#window.layout.addWidget(self.fig.native, 0, 0) 
window.show()
#sys.exit(app.exec_())