# -*- coding: utf-8 -*-
"""
Created on Sat Mar 25 05:57:50 2017

@author: marzipan
"""

import numpy as np
from vispy import plot as vp
from vispy import app
from pylsl import StreamInlet, resolve_stream
import time

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


colors = [(0.8, 0, 0, 1),
          (0.8, 0, 0.8, 1),
          (0, 0, 1.0, 1),
          (0, 0.7, 0, 1), 
          (0.18, 0, 0, 1),
          (0.18, 0, 0.8, 1),
          (0.1, 0, 1.0, 1),
          (0.1, 0.7, 0, 1),]
          
lines = []


for i in range(8):
    lines += [fig[0, 0].plot(y[i,:], color=colors[i])]
    

grid = vp.visuals.GridLines(color=(0, 0, 0, 0.5))
grid.set_gl_state('translucent')
fig[0, 0].view.add(grid)

idx = 0
begin = time.time()
def update_plot(event):
    global lines,y,fig,colors,idx,begin
    if idx==0: begin = time.time()
    idx+=1
    if idx %100 == 0:
        print("fps: ",idx/(time.time()-begin))
   
    try:
        #time.sleep(0) #yield 
        sample, timestamp = inlet.pull_sample()
        #print(sample[0])
        new_samples = np.asarray(sample)
        k = 1
        y[:, :-k] = y[:, k:]
        y[:, -k:] = new_samples[:,None]     
        
        #normalize 
        ymax = y.max()
        if ymax > 0:
            yn = y/(ymax*1.2)
        else:
            yn = y.copy()
        
        for i,line in enumerate(lines):
            line.set_data(yn[i,:]+i, color=colors[i])

        fig.update()

        
    except RuntimeError as err:
        if 'EventEmitter loop detected' in err.args[0]: #TODO handle this correctly
            pass

timer = app.Timer()
timer.connect(update_plot)
timer.start(1.0/ 200)

if __name__ == '__main__':
    fig.show(run=True)

    
