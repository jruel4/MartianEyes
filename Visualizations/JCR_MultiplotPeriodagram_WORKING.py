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
    streams = resolve_stream('type', 'EEG')
    for i,s in enumerate(streams):
        print(i,s.name())
    stream_id = input("Input desired stream id: ")
    inlet = StreamInlet(streams[int(stream_id)])    
    return inlet

inlet = select_stream()

NCHAN = 1
rows = 1
cols = 1

# dynamically get length and nchan
sample_tst, _ts = inlet.pull_sample()


# vertex positions of data to draw
N = len(sample_tst) + 2
pos = np.zeros((NCHAN, N, 2), dtype=np.float32)
x_lim = [0., float(N)]
y_lim = [-2., 2.]
pos[:,:, 0] = np.linspace(x_lim[0], x_lim[1], N)
pos[:,:, 1] = np.random.normal(size=N)

# color array
color = np.ones((N, 4), dtype=np.float32)
color[:, 0] = np.linspace(0, 1, N)
color[:, 1] = color[::-1, 0]

canvas = scene.SceneCanvas(keys=None, show=True)
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


def update(ev):
    global pos, color, lines,inlet,conv2uv
    
    (samples, timestamps) = inlet.pull_sample()

    # Check if we actually received any samples - pull_chunk doesn't block
    k = len(samples)
    if k == 0:
        return
    
    new_samples = np.transpose(samples)
    pos[:,:-k, 1] = pos[:,k:,1]
    pos[:,-k:, 1] = new_samples

    sc_pos = pos.copy()

    # normalize
#    yn = np.zeros_like(pos)
#        print "YN", yn.shape
#    for i in range(1):
#        yn[i,:] = (pos[i,:]/max(abs(pos[i,:])*2.0)) + 0.5
    
    color = np.roll(color, 1, axis=0)
    for i in range(len(lines)):
        lines[i].set_data(pos=sc_pos[i,:,:], color=color)

timer = app.Timer(iterations=1000)
timer.connect(update)
timer.start(0)

if __name__ == '__main__' and sys.flags.interactive == 0:
    app.run()
