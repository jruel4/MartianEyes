# -*- coding: utf-8 -*-
"""
Created on Sun Jul 16 01:12:32 2017

@author: marzipan
"""








# -*- coding: utf-8 -*-
"""
Created on Sat Jul 15 23:46:01 2017

@author: marzipan
"""

# e2a5 - dev1
# d0c9 - dev2

import sys
import numpy as np
import time
from vispy import app as vp_app
from vispy import scene


from pylsl import StreamInlet, resolve_stream

streams = list()
def select_stream():
    streams = resolve_stream()
    for i,s in enumerate(streams):
        print i,s.name(), s.uid()
    stream_id = input("Input desired stream id: ")
    inlet = StreamInlet(streams[int(stream_id)])    
    return inlet

inlet = select_stream()

G_NChanPlot = 8
G_NChanPlot_IDX = range(G_NChanPlot)

G_FS = 250

rows = 4
cols = 2

G_MovingAverageLen = 1
G_RemoveDC = False

# vertex positions of data to draw
G_LenSigPlot = 10000
pos = np.zeros((G_NChanPlot, G_LenSigPlot, 2), dtype=np.float32)
x_lim = [-1. * G_LenSigPlot / G_FS, 0.]
pos[:,:, 0] = np.linspace(x_lim[0], x_lim[1], G_LenSigPlot)

# color array
color = np.ones((G_LenSigPlot, 4), dtype=np.float32)
color[:, 0] = np.linspace(0, 1, G_LenSigPlot)
color[:, 1] = color[::-1, 0]

# Build canvas
canvas = scene.SceneCanvas(keys=None, show=False)
grid = canvas.central_widget.add_grid(spacing=50)

lines = list()
viewboxes = list()
for r in range(rows):
    for c in range(cols):
        viewboxes.append(grid.add_view(row=r*2, col=c, camera='panzoom'))
    
        # add some axes
        x_axis = scene.AxisWidget(orientation='bottom')
        x_axis.stretch = (1, 0.1)
        grid.add_widget(x_axis, row=1+r*2, col=c,col_span=1, row_span=1)
        x_axis.link_view(viewboxes[c + r*cols])
        y_axis = scene.AxisWidget(orientation='left')
        y_axis.stretch = (0.1, 1)
        grid.add_widget(y_axis, row=0+r*2, col=c)
        y_axis.link_view(viewboxes[c + r*cols])
    
        # add a line plot inside the viewbox
        lines.append(scene.Line(pos[c + r*cols,:,:], color, parent=viewboxes[c + r*cols].scene))
        
        # auto-scale to see the whole line.
        viewboxes[c + r*cols].camera.set_range()


conv2uv = False
conv2uvfromv = True
groov = None
idx=0


i2v = ( (4.5 / (2**23 - 1)) / 24)
once = True
last_upd = 0


# Moving average length must be greater than 1
#assert G_MovingAverageLen >= 1

#buflen = 5000
#G_MABuffer = np.zeros([buflen,G_NChanIn,G_LenSigIn])


def update(ev):
    global pos, color, lines,inlet,conv2uv,groov,idx,last_upd,once
    idx +=1
    (samples, timestamps) = inlet.pull_chunk(max_samples=250)

    # Check if we actually received any samples - pull_chunk doesn't block
    k = len(samples)
    if k == 0:
        return
    
    # new_samples shape: (nchan, nsamples)
    new_samples = np.transpose(samples)
    
    new_samples = new_samples[:min([G_NChanPlot,len(new_samples)]), :]
    pos[:,:-k, 1] = pos[:,k:,1]
    pos[:,-k:, 1] = new_samples

    sc_pos = pos.copy()
    groov = sc_pos.copy()
    if conv2uv:        
        sc_pos[:,:,1] *= i2v * 1000000.0
    if conv2uvfromv:
        sc_pos[:,:,1] *= 1000000.0
    if G_RemoveDC:
        sc_pos[:,:,1] -= np.sum(sc_pos[:,:,1]) / len(sc_pos[:,:,1])
        if once:
            print sc_pos.shape
            once = False

    color = np.roll(color, 10, axis=0)

    for i in range(len(lines)):
        lines[i].set_data(pos=sc_pos[i,:,:], color=color)

    if (time.time() - last_upd) > 1.0:
        for i in range(len(viewboxes)):
            viewboxes[i].camera.set_range(y= (max([min(sc_pos[i,:,1]),0]), max(sc_pos[i,:,1]) ) )
        last_upd = time.time()

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
    
    Layout.addWidget(canvas.native, 0, 0) 
    canvas.show()
    canvas.measure_fps()
    Window.show()
    
    a0 = vp_app.Application()
    vp_app.use_app(a0)
    timer = vp_app.Timer(iterations=100)
    timer.connect(update)
    timer.start(0)
    
    sys.exit(qt_app.exec_())