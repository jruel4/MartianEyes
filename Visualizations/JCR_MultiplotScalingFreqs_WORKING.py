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
from scipy import signal
from vispy import app, scene


from pylsl import StreamInlet, resolve_stream

streams = list()
def select_stream():
    streams = resolve_stream()
    for i,s in enumerate(streams):
        print i, s.name(), s.uid()
    stream_id = input("Input desired stream id: ")
    inlet = StreamInlet(streams[int(stream_id)])    
    return inlet

inlet = select_stream()

G_NChanPlot = 4
G_NChanPlot_IDX = range(4)
#G_NChanPlot_IDX = np.arange(18,34,4)

G_FS = 250

rows = 2
cols = 2

G_MovingAverageLen = 1
G_RemoveDC = False
G_RemoveNegatives = False

buflen = 10000
G_MABuffer = np.zeros([G_NChanPlot,buflen])

# vertex positions of data to draw
G_LenSigPlot = 10000 - G_MovingAverageLen + 1
pos = np.zeros((G_NChanPlot, G_LenSigPlot, 2), dtype=np.float32)
x_lim = [-1*G_LenSigPlot / G_FS, 0.]
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

        y_axis = scene.AxisWidget(orientation='right')
        y_axis.stretch = (0.1, 1)
        grid.add_widget(y_axis, row=0+r*2, col=c)
        y_axis.link_view(viewboxes[c + r*cols])
    
        # add a line plot inside the viewbox
        lines.append(scene.Line(pos[c + r*cols,:,:], color, parent=viewboxes[c + r*cols].scene))
        
        # auto-scale to see the whole line.
        viewboxes[c + r*cols].camera.set_range()


conv2uv = False
conv2uvfromv = False
groov = None
idx=0


i2v = ( (4.5 / (2**23 - 1)) / 24)
once = True
last_upd = 0


# Moving average length must be greater than 1
assert G_MovingAverageLen >= 1

def update(ev):
    global pos, color, lines,inlet,conv2uv,groov,idx,last_upd,once,G_MABuffer
    idx +=1
    # Samples is (samples, nchan)
    (samples, timestamps) = inlet.pull_chunk(max_samples=buflen-1)

    # Check if we actually received any samples - pull_chunk doesn't block
    k = len(samples)
    if k == 0:
        return

    # new_samples shape: (nchan, nsamples)
    samples_tmp = np.transpose(samples)    

    # Shift the moving average buffer
    G_MABuffer[:,:-k] = G_MABuffer[:,k:]
    # Update the newest values
    G_MABuffer[:,-k:] = samples_tmp[G_NChanPlot_IDX,:]
    
    # Convolve kernel for smoothing
    ma_kernel = np.ones((1,G_MovingAverageLen))
    if G_RemoveNegatives:
        G_MABufferMask = (G_MABuffer >= 0) * 1
    else:
        G_MABufferMask = np.ones_like(G_MABuffer)
        
    G_MABuffer = G_MABuffer * G_MABufferMask
    G_MABufferSmoothed = signal.convolve2d(G_MABuffer, ma_kernel,mode='valid',fillvalue=1)
    n_samples_per_point = signal.convolve2d(G_MABufferMask, ma_kernel,mode='valid',fillvalue=1)
    
    zeros = (n_samples_per_point == 0)
    zeros = zeros*1
    n_samples_per_point += zeros
    smoothed_signal = G_MABufferSmoothed / n_samples_per_point


#    if once: print "(MA)New samples, shape: ", np.shape(G_MABuffer[-G_MovingAverageLen:, :, :] / float(G_MovingAverageLen))
    groov = smoothed_signal
    pos[:,:,1] = smoothed_signal

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

#==============================================================================
#     if (time.time() - last_upd) > 1.0:
#         for i in range(len(viewboxes)):
#             if G_RemoveNegatives:
#                 viewboxes[i].camera.set_range(y= (max([min(sc_pos[i,:,1]),0]), max(sc_pos[i,:,1]) ) )
#             else:
#                 viewboxes[i].camera.set_range(y= (min(sc_pos[i,:,1]), max(sc_pos[i,:,1]) ) )
#         last_upd = time.time()
#==============================================================================

timer = app.Timer(iterations=10000)
timer.connect(update)
timer.start(0)

time.sleep(0.5)
canvas.show()

if __name__ == '__main__' and sys.flags.interactive == 0:
    app.run()
