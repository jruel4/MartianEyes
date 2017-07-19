# -*- coding: utf-8 -*-
"""
Created on Wed Jul 19 01:11:04 2017

@author: marzipan
"""

import numpy as np
import sys

from vispy import app as v_app
from vispy import gloo, visuals

# vertex positions of data to draw
N = 20
pos = np.zeros((N, 2), dtype=np.float32)
pos[:, 0] = np.linspace(10, 790, N)
pos[:, 1] = np.random.normal(size=N, scale=100, loc=400)


class Canvas(v_app.Canvas):
    def __init__(self,appy):
        v_app.Canvas.__init__(self, keys='interactive',
                            size=(800, 800),app=appy)
        self.line = visuals.LinePlotVisual(pos, color='w', edge_color='w',
                                           symbol='o', 
                                           face_color=(0.2, 0.2, 1))
        self.show()

    def on_draw(self, event):
        gloo.clear('black')
        self.line.draw()

    def on_resize(self, event):
        # Set canvas viewport and reconfigure visual transforms to match.
        vp = (0, 0, self.physical_size[0], self.physical_size[1])
        self.context.set_viewport(*vp)
        self.line.transforms.configure(canvas=self, viewport=vp)




import sys
from PySide.QtCore import *
from PySide.QtGui import * 


if __name__ == '__main__' and sys.flags.interactive == 0:

    try:
        qt_app = QApplication([])
    except RuntimeError:
        print "Qt Application Already Exists"
        pass
    
    Window = QWidget()
    Window.setGeometry(0,0,500,800)
    Window.setWindowTitle("Multiplot")
    Layout = QGridLayout()
    Window.setLayout(Layout)


    a0 = v_app.Application()
    a1 = v_app.Application()
    win = Canvas(appy=a0)
    win2 = Canvas(appy=a1)
    if sys.flags.interactive != 1:
        a0.run()
        a1.run()


    Layout.addWidget(win.native, 0, 0) 
    Layout.addWidget(win2.native, 1, 1) 

    Window.show()
    
    sys.exit(qt_app.exec_())    