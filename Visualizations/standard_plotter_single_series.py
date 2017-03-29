# -*- coding: utf-8 -*-
"""
Created on Sun Mar 26 08:34:52 2017

@author: marzipan
"""

import numpy as np
from vispy import plot as vp
from vispy import app
import threading
from pylsl import StreamInlet, resolve_stream
import time
from PySide.QtCore import QTimer
from PySide.QtGui import QApplication

streams = list()
def select_stream():
    streams = resolve_stream('type', 'EEG')
    for i,s in enumerate(streams):
        print(i,s.name())
    stream_id = input("Input desired stream id: ")
    inlet = StreamInlet(streams[int(stream_id)])    
    return inlet
    
inlet = select_stream()

fig = vp.Fig(size=(800, 800), show=False)

x = np.linspace(0, 10, 20)
xn = x.copy()
y = np.ones((8,600)) * 8.1
y[:,0]=-1
yn = np.zeros_like(y)


colors = [(0.8, 0, 0, 1),
          (0.8, 0, 0.8, 1),
          (0, 0, 1.0, 1),
          (0, 0.7, 0, 1), 
          (0.18, 0, 0, 1),
          (0.18, 0, 0.8, 1),
          (0.1, 0, 1.0, 1),
          (0.1, 0.7, 0, 1),]
          
lines = []


for i in range(1):
    lines += [fig[0, 0].plot(y[i,:], color=colors[i])]
    

grid = vp.visuals.GridLines(color=(0, 0, 0, 0.5))
grid.set_gl_state('translucent')
fig[0, 0].view.add(grid)

def update_plot(event):
    global lines,y,fig,colors,yn
    #print("fart")
    #while True:
        
    try:
        time.sleep(0.010) #yield 
        sample, timestamp = inlet.pull_sample()
        new_samples = np.asarray(sample)
        k = 1
        y[:, :-k] = y[:, k:]
        y[:, -k:] = new_samples[:,None]     
        
        #normalize 
        ymax = y.max()
        #TODO put this check back in! if ymax > 1.0:
        yn = y/(ymax*1.2)
        
        for i,line in enumerate(lines):
            line.set_data(yn[i,:]+i, color=colors[i])
        
    except RuntimeError as err:
        if 'EventEmitter loop detected' in err.args[0]: #TODO handle this correctly
            pass

timer = app.Timer()
timer.connect(update_plot)
timer.start(.016)

if __name__ == '__main__':
    fig.show(run=True)




