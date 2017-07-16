# -*- coding: utf-8 -*-
"""
Created on Sat Jul 15 23:46:01 2017

@author: marzipan
"""

import sys
import numpy as np
from vispy import app, scene

# vertex positions of data to draw
N = 100
pos = np.zeros((N, 2), dtype=np.float32)
x_lim = [50., 750.]
y_lim = [-2., 2.]
pos[:, 0] = np.linspace(x_lim[0], x_lim[1], N)
pos[:, 1] = np.random.normal(size=N)

# color array
color = np.ones((N, 4), dtype=np.float32)
color[:, 0] = np.linspace(0, 1, N)
color[:, 1] = color[::-1, 0]

canvas = scene.SceneCanvas(keys=None, show=True)
grid = canvas.central_widget.add_grid(spacing=0)

lines = list()
viewboxes = list()
for i in range(1):
    viewboxes.append(grid.add_view(row=i*2, col=1, camera='panzoom'))

    # add some axes
    x_axis = scene.AxisWidget(orientation='bottom')
    x_axis.stretch = (1, 0.1)
    grid.add_widget(x_axis, row=1+i*2, col=1)#,col_span=2)
    x_axis.link_view(viewboxes[i])
    y_axis = scene.AxisWidget(orientation='left')
    y_axis.stretch = (0.1, 1)
    grid.add_widget(y_axis, row=0+i*2, col=0)
    y_axis.link_view(viewboxes[i])

    # add a line plot inside the viewbox
    lines.append(scene.Line(pos, color, parent=viewboxes[i].scene))
    
    # auto-scale to see the whole line.
    viewboxes[i].camera.set_range()


def update(ev):
    global pos, color, lines
    pos[:, 1] = np.random.normal(size=N)
    color = np.roll(color, 1, axis=0)
    for i in range(len(lines)):
        lines[i].set_data(pos=pos, color=color)

timer = app.Timer(iterations=-1)
timer.connect(update)
timer.start(0)

if __name__ == '__main__' and sys.flags.interactive == 0:
    app.run()
