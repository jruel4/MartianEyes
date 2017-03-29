# -*- coding: utf-8 -*-
"""
Created on Sun Mar 26 10:20:42 2017

@author: marzipan
"""

import numpy as np
from vispy import plot as vp
from vispy import app
from pylsl import StreamInlet, resolve_stream

streams = list()
def select_stream():
    streams = resolve_stream('type', 'EEG')
    for i,s in enumerate(streams):
        print(i,s.name())
    stream_id = input("Input desired stream id: ")
    inlet = StreamInlet(streams[int(stream_id)])    
    return inlet
    
inlet = select_stream()

fig = vp.Fig(size=(800, 400), show=False)
spec = fig[0,0].plot(np.zeros((129)))

ch_sel = 0

def update_plot(event):
    global inlet, new_data, spec, sample, ch_sel
    sample, timestamp = inlet.pull_sample()
    sample = np.asarray(sample)
    sample = sample.reshape((129,8))
    ch1_samples = sample[:,ch_sel]
    spec.set_data(ch1_samples)
    spec.update()

timer = app.Timer()
timer.connect(update_plot)
timer.start(0.016)

if __name__ == '__main__':
    fig.show(run=True)
    
    
    
    
    
