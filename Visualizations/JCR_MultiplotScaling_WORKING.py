# -*- coding: utf-8 -*-
"""
Created on Sat Jul 15 23:46:01 2017

@author: marzipan
"""

import sys
import numpy as np
from vispy import app, scene


from pylsl import StreamInlet, resolve_stream

streams = list()
def select_stream():
    streams = resolve_stream()
    for i,s in enumerate(streams):
        print(i,s.name())
    stream_id = input("Input desired stream id: ")
    inlet = StreamInlet(streams[int(stream_id)])    
    return inlet

inlet = select_stream()

G_NChanPlot = 2
rows = 2
cols = 1


# vertex positions of data to draw
G_LenSigPlot = 10000
pos = np.zeros((G_NChanPlot, G_LenSigPlot, 2), dtype=np.float32)
x_lim = [-1*G_LenSigPlot, 0.]
y_lim = [-2., 2.]
pos[:,:, 0] = np.linspace(x_lim[0], x_lim[1], G_LenSigPlot)
pos[:,:, 1] = np.random.normal(size=G_LenSigPlot)

# color array
color = np.ones((G_LenSigPlot, 4), dtype=np.float32)
color[:, 0] = np.linspace(0, 1, G_LenSigPlot)
color[:, 1] = color[::-1, 0]

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


conv2uv = True
groov = None
def scale_to_volts(raw, gain = 24, vref = 4.5):
     return  raw * ( (vref / (2**23 - 1)) / gain)

def update(ev):
    global pos, color, lines,inlet,conv2uv,groov
    
    (samples, timestamps) = inlet.pull_chunk(max_samples=250)

    # Check if we actually received any samples - pull_chunk doesn't block
    k = len(samples)
    if k == 0:
        return
    
    new_samples = np.transpose(samples)
#    print new_samples.shape
    new_samples = new_samples[:min([G_NChanPlot,len(new_samples)]), :]
    pos[:,:-k, 1] = pos[:,k:,1]
    pos[:,-k:, 1] = new_samples

    sc_pos = pos.copy()
    groov = sc_pos.copy()
    if conv2uv:        
        sc_pos[:,:,1] = scale_to_volts(sc_pos[:,:,1]) * 1000000.0

    # normalize
#    yn = np.zeros_like(pos)
#        print "YN", yn.shape
#    for i in range(1):
#        yn[i,:] = (pos[i,:]/max(abs(pos[i,:])*2.0)) + 0.5
    
    color = np.roll(color, 1, axis=0)
    for i in range(len(lines)):
        lines[i].set_data(pos=sc_pos[i,:,:], color=color)

timer = app.Timer(iterations=5000)
timer.connect(update)
timer.start(0)

import time
time.sleep(0.5)
canvas.show()

if __name__ == '__main__' and sys.flags.interactive == 0:
    app.run()
