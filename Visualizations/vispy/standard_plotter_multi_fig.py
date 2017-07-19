# -*- coding: utf-8 -*-
"""
Created on Sat Mar 25 07:07:02 2017

@author: marzipan
"""

# -*- coding: utf-8 -*-
"""
BUGGY!
"""

import numpy as np
from vispy import plot as vp
import threading
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
y = np.ones((8,600))
y[:,0] = 1.5
y[:,1] = -1.5

lines = []

for i in range(4):
    for j in range(2):
        lines += [fig[i, j].plot(y[i,:])]
                      
#==============================================================================
# grid = vp.visuals.GridLines(color=(0, 0, 0, 0.5))
# grid.set_gl_state('translucent')
# fig[0, 0].view.add(grid)
#==============================================================================

def update_plot():
    global lines,y,fig
    idx = 0
    while True:
        idx += 1
        time.sleep(0.010)
        try:

            sample, timestamp = inlet.pull_sample()
            new_samples = np.asarray(sample)
            k = 1
            y[:, :-k] = y[:, k:]
            y[:, -k:] = new_samples[:,None]     
            
            for i,line in enumerate(lines):
                line.set_data(y[i,:])
                
            fig.update()
        except Exception as e:
            print("idx: ",idx,e)
            
        
if __name__ == '__main__':
    fig.show(run=True)
#==============================================================================
#     thread = threading.Thread(target=update_plot)
#     thread.start()
#==============================================================================
    

#==============================================================================
# thread = threading.Thread(target=update_plot)
# thread.start()
# 
# 
#==============================================================================


