
"""
This example demonstrates the different auto-ranging capabilities of ViewBoxes
"""

import numpy as np
import time

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg

from Utils.lsl_utils import select_stream


inlet = select_stream()


win = pg.GraphicsWindow(title="Plot auto-range examples")
win.resize(800,600)
win.setWindowTitle('pyqtgraph example: PlotAutoRange')



curve=list()
for i in range(4):
    for j in range(2):
        p2 = win.addPlot(title="Auto Pan Only")
        #p2.setAutoPan(y=True)
        #p2.enableAutoRange()
        curve.append(p2.plot(pen=pg.intColor(i*8+j, hues=8)))
    win.nextRow()


y = np.random.randn(64, 1000).astype(np.float32)

idx=1.0
first=True
def update():
    global first, begin,idx
    if first:
        begin = pg.time()
        first = False

    # Samples is (samples, nchan)
    (samples, timestamps) = inlet.pull_chunk(max_samples=1000-1)

    # Check if we actually received any samples - pull_chunk doesn't block
    k = len(samples)
    if k == 0:
        return

    # new_samples shape: (nchan, nsamples)    
    new_samples = np.transpose(samples)

    y[:, :-k] = y[:, k:]
    y[:, -k:] = new_samples[:,:]
    
    global curve
    for i in range(8):
        curve[i].setData(y[i,:])
    
    if idx%20 == 0:
        win.setWindowTitle('FPS: ' + str(idx / (pg.time() - begin)))
    idx+=1
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()