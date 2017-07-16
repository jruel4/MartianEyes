# -*- coding: utf-8 -*-
"""
Created on Sat Jul 15 02:32:32 2017

@author: marzipan
"""


from vispy import app, gloo, visuals
import numpy as np


def generate_idx(rows, cols, buf_size):
    return np.asarray([[r,c,idx] for r in range(rows) for c in range(cols) for idx in range(buf_size)])

# size of canvas and graph
G_CanvasSize = (800, 600)
G_GraphEdgeMargins = (50,50) # space from sides of graph to edge of canvas (w x h)
G_GraphMargins = (50,50) # space between one graph and another graph (w x h)

# Global variables
G_GraphCols = 2
G_GraphRows = 4
G_MaximumBufferTime = 5000 # in samples, NOT seconds

G_GraphWidth = (G_CanvasSize[0] - G_GraphEdgeMargins[0]*2 - G_GraphMargins[0]*(G_GraphCols-1)) / G_GraphCols
G_GraphHeight = (G_CanvasSize[1] - G_GraphEdgeMargins[1]*2 - G_GraphMargins[1]*(G_GraphRows-1)) / G_GraphRows


# generate sizes of individual graphs
curcol = 1
currow = 1

def get_x_axis_coord(currow, curcol):
    return np.asarray([
        [G_GraphEdgeMargins[0] + curcol * (G_GraphMargins[0]  + G_GraphWidth), G_CanvasSize[1] - (G_GraphEdgeMargins[1] + currow * (G_GraphMargins[1] + G_GraphHeight))],
        [G_GraphEdgeMargins[0] + curcol * (G_GraphMargins[0] + G_GraphWidth) + G_GraphWidth, G_CanvasSize[1] - (G_GraphEdgeMargins[1] + currow * (G_GraphMargins[1] + G_GraphHeight))]
        ])

def get_y_axis_coord(currow, curcol):
    return np.asarray([
        [G_GraphEdgeMargins[0] + curcol * (G_GraphMargins[0] + G_GraphWidth), G_GraphEdgeMargins[1] + currow * (G_GraphMargins[1] + G_GraphHeight) + G_GraphHeight],
        [G_GraphEdgeMargins[0] + curcol * (G_GraphMargins[0] + G_GraphWidth), G_GraphEdgeMargins[1] + currow * (G_GraphMargins[1] + G_GraphHeight)]
        ])

x_axis_positions = [get_x_axis_coord(r,c) for r in range(G_GraphRows) for c in range(G_GraphCols)]
y_axis_positions = [get_y_axis_coord(r,c) for r in range(G_GraphRows) for c in range(G_GraphCols)]

# Calculate 2D index of each vertex (row and col) and x-index (sample index within each signal).
G_ShaderMapping = generate_idx(G_GraphRows, G_GraphCols, G_MaximumBufferTime)




e = None
a = None
class Canvas(app.Canvas):
    def __init__(self):
#        self.g = gloo.Program(vertex,fragment)
#        self.g['a_position'] = np.c_[
#            np.linspace(-1.0, +1.0, 1000),
#            np.random.uniform(-0.5, +0.5, 1000)].astype(np.float32)
        self.axis_start = 0.0
        self.axis_end = 1.0
        self.x_axes = [visuals.AxisVisual(x_ax, (0, 100), (0., 1.)) for x_ax in x_axis_positions]
        self.y_axes = [visuals.AxisVisual(y_ax) for y_ax in y_axis_positions]
        app.Canvas.__init__(self, size=G_CanvasSize, title='Glyphs', keys='interactive',show=True)
        
    def on_draw(self, event):
        gloo.clear('black')
        for x in self.x_axes:
            x.draw()
        for y in self.y_axes:
            y.draw()
#        self.g.draw('line_strip')

    def on_mouse_wheel(self, event):
        print "Event: ", event
        global e
        e = event

    def on_resize(self, event):
        # Set canvas viewport and reconfigure visual transforms to match.
        vp = (0, 0, self.physical_size[0], self.physical_size[1])
        self.context.set_viewport(*vp)
        for x in self.x_axes:
            x.transforms.configure(canvas=self, viewport=vp)
        for y in self.y_axes:
            y.transforms.configure(canvas=self, viewport=vp)
#        self.x_axes.transforms.configure(canvas=self, viewport=vp)


if __name__ == '__main__':
    c = Canvas()
    c.show()
    app.run()    

vertex = """
attribute vec2 a_position;
void main (void)
{
    gl_Position = vec4(a_position, 0.0, 1.0);
}
"""

fragment = """
void main()
{
    gl_FragColor = vec4(1.0, 1.0, 1.0, 1.0);
}
"""