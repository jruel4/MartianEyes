# -*- coding: utf-8 -*-
"""
Created on Fri Mar 24 15:17:49 2017

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
#sample, timestamp = inlet.pull_sample()

fs=250
fig = vp.Fig(show=False)

'''
_colormaps = dict(
    # Some colormap presets
    autumn=Colormap([(1., 0., 0., 1.), (1., 1., 0., 1.)]),
    blues=Colormap([(1., 1., 1., 1.), (0., 0., 1., 1.)]),
    cool=Colormap([(0., 1., 1., 1.), (1., 0., 1., 1.)]),
    greens=Colormap([(1., 1., 1., 1.), (0., 1., 0., 1.)]),
    reds=Colormap([(1., 1., 1., 1.), (1., 0., 0., 1.)]),
    spring=Colormap([(1., 0., 1., 1.), (1., 1., 0., 1.)]),
    summer=Colormap([(0., .5, .4, 1.), (1., 1., .4, 1.)]),
    fire=_Fire(),
    grays=_Grays(),
    hot=_Hot(),
    ice=_Ice(),
    winter=_Winter(),
    light_blues=_SingleHue(),
    orange=_SingleHue(hue=35),
    viridis=Colormap(ColorArray(_viridis_data[::2])),
    # Diverging presets
    coolwarm=Colormap(ColorArray(
        [
            (226, 0.59, 0.92), (222, 0.44, 0.99), (218, 0.26, 0.97),
            (30, 0.01, 0.87),
            (20, 0.3, 0.96), (15, 0.5, 0.95), (8, 0.66, 0.86)
        ],
        color_space="hsv"
    )),
    PuGr=_Diverging(145, 280, 0.85, 0.30),
    GrBu=_Diverging(255, 133, 0.75, 0.6),
    GrBu_d=_Diverging(255, 133, 0.75, 0.6, "dark"),
    RdBu=_Diverging(220, 20, 0.75, 0.5),

    # Configurable colormaps
    cubehelix=CubeHelixColormap,
    single_hue=_SingleHue,
    hsl=_HSL,
    husl=_HUSL,
    diverging=_Diverging
)
'''

spec = list()
for r in range(4):
    for c in range(2):        
        spec += [fig[r,c].spectrogram(np.zeros((256*200)), fs=fs, clim=(0, 1), cmap='fire')]

new_data = spec[0]._data
new_data = np.zeros_like(new_data)

new_datas = [np.zeros_like(new_data) for i in range(8)]

cmin = 0
cmax = 1



def update_plot(event):
    global inlet, new_data, spec, sample, cmin, cmax


    
    sample, timestamp = inlet.pull_sample()
    sample = np.asarray(sample)
    sample = sample.reshape((129,8))
    for idx in range(8):
        ch_samples = sample[:,idx]
        k = 1
        new_datas[idx][:, :-k] = new_datas[idx][:, k:]
        new_datas[idx][:, -k:] = ch_samples[:,None]
        
        #normalize
        d = new_datas[idx]/new_datas[idx].max()
        spec[idx].set_data(d)

timer = app.Timer()
timer.connect(update_plot)
timer.start(0.016)

if __name__ == '__main__':
    fig.show(run=True)
#==============================================================================
#     thread = Thread(target=update)
#     thread.start()
#==============================================================================
    
    
    