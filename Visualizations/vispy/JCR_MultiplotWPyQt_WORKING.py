# -*- coding: utf-8 -*-
"""
Created on Sat Jul 15 00:50:22 2017

@author: marzipan
"""

from vispy import gloo, visuals, app
from line_profiler import LineProfiler
from pylsl import StreamInlet, resolve_stream
import numpy as np
import time
from threading import Thread, Event





# TODO
# 1. Make this a class, kill ALL global variables
# 2. Make all graph dimensions relative

G_TIME_IT = 0
def time_it(start0_stop1):
    global G_TIME_IT
    if start0_stop1 > 0.5:
        G_TIME_IT = time.time()
    elif start0_stop1 < 0.5:
        print "Time taken: ", time.time() - G_TIME_IT

def generate_idx(rows, cols, buf_size):
    return np.asarray([[c,r,idx] for r in range(rows) for c in range(cols) for idx in np.linspace(0,1.0,buf_size)])



# Size of canvas in pixels
G_Pix_CanvasWidth = 1600.
G_Pix_CanvasHeight = 800.
G_Pix_GraphEdgeMargins = (75.,50.) # space from sides of graph to edge of canvas (w x h)
G_Pix_GraphMargins = (75.,50.) # space between one graph and another graph (w x h)

G_NumChannels = 64
G_GraphCols = 8
G_GraphRows = 8
G_MaximumBufferSize = 1000 # in samples, NOT seconds

# Calculated values
G_Pix_CanvasSize = (G_Pix_CanvasWidth, G_Pix_CanvasHeight)
G_Pix_GraphWidth = (G_Pix_CanvasWidth - G_Pix_GraphEdgeMargins[0]*2.0 - G_Pix_GraphMargins[0]*(G_GraphCols-1.0)) / G_GraphCols
G_Pix_GraphHeight = (G_Pix_CanvasHeight - G_Pix_GraphEdgeMargins[1]*2.0 - G_Pix_GraphMargins[1]*(G_GraphRows-1.0)) / G_GraphRows
G_Pix_GraphSize = (G_Pix_GraphWidth, G_Pix_GraphHeight)

G_Rel_GraphWidth = G_Pix_GraphWidth / G_Pix_CanvasWidth
G_Rel_GraphHeight = G_Pix_GraphHeight / G_Pix_CanvasHeight
G_Rel_GraphSize = (G_Rel_GraphWidth, G_Rel_GraphHeight)
G_Rel_GraphEdgeMargins = (G_Pix_GraphEdgeMargins[0] / G_Pix_CanvasSize[0], G_Pix_GraphEdgeMargins[1] / G_Pix_CanvasSize[1])
G_Rel_GraphMargins = (G_Pix_GraphMargins[0] / G_Pix_CanvasSize[0], G_Pix_GraphMargins[1] / G_Pix_CanvasSize[1])

# Validate that all relative values add up to 1
assert (G_Rel_GraphWidth*G_GraphCols + G_Rel_GraphEdgeMargins[0]*2.0 + G_Rel_GraphMargins[0]*(G_GraphCols-1.0)) == 1.0, "Error, relative width dimensions must add up to 1.0"
assert (G_Rel_GraphHeight*G_GraphRows + G_Rel_GraphEdgeMargins[1]*2.0 + G_Rel_GraphMargins[1]*(G_GraphRows-1.0)) == 1.0, "Error, relative height dimensions must add up to 1.0"

# Color of each vertex (TODO: make it more efficient by using a GLSL-based
# color map and the index).
G_ColorMap = np.repeat(np.random.uniform(size=(G_NumChannels, 3), low=.5, high=.9),
                  G_MaximumBufferSize, axis=0).astype(np.float32)

# Generate the total number of shaders we'll be using (won't need this in the future!)
G_TotalShaders = G_NumChannels * G_MaximumBufferSize

# Calculate 2D index of each vertex (row and col) and x-index (sample index within each signal).
G_Rel_ShaderMapping = generate_idx(G_GraphRows, G_GraphCols, G_MaximumBufferSize)
#G_ShaderMapping = G_ShaderMapping / [1.,1., float(G_MaximumBufferSize - 1)]

# generate sizes of individual graphs
def get_x_axis_coord(currow, curcol):
    return np.asarray([
        [G_Pix_GraphEdgeMargins[0] + curcol * (G_Pix_GraphMargins[0] + G_Pix_GraphWidth), G_Pix_CanvasSize[1] - (G_Pix_GraphEdgeMargins[1] + currow * (G_Pix_GraphMargins[1] + G_Pix_GraphHeight))],
        [G_Pix_GraphEdgeMargins[0] + curcol * (G_Pix_GraphMargins[0] + G_Pix_GraphWidth) + G_Pix_GraphWidth, G_Pix_CanvasSize[1] - (G_Pix_GraphEdgeMargins[1] + currow * (G_Pix_GraphMargins[1] + G_Pix_GraphHeight))]
        ])

def get_y_axis_coord(currow, curcol):
    return np.asarray([
        [G_Pix_GraphEdgeMargins[0] + curcol * (G_Pix_GraphMargins[0] + G_Pix_GraphWidth), G_Pix_GraphEdgeMargins[1] + currow * (G_Pix_GraphMargins[1] + G_Pix_GraphHeight) + G_Pix_GraphHeight],
        [G_Pix_GraphEdgeMargins[0] + curcol * (G_Pix_GraphMargins[0] + G_Pix_GraphWidth), G_Pix_GraphEdgeMargins[1] + currow * (G_Pix_GraphMargins[1] + G_Pix_GraphHeight)]
        ])

def get_x_axis_coord_rel(currow, curcol):
    return np.asarray([
        [G_Rel_GraphEdgeMargins[0] + curcol * (G_Rel_GraphMargins[0] + G_Rel_GraphWidth), 1.0 - (G_Rel_GraphEdgeMargins[1] + currow * (G_Rel_GraphMargins[1] + G_Rel_GraphHeight))],
        [G_Rel_GraphEdgeMargins[0] + curcol * (G_Rel_GraphMargins[0] + G_Rel_GraphWidth) + G_Rel_GraphWidth, 1.0 - (G_Rel_GraphEdgeMargins[1] + currow * (G_Rel_GraphMargins[1] + G_Rel_GraphHeight))]
        ])

def get_y_axis_coord_rel(currow, curcol):
    return np.asarray([
        [G_Rel_GraphEdgeMargins[0] + curcol * (G_Rel_GraphMargins[0] + G_Rel_GraphWidth), G_Rel_GraphEdgeMargins[1] + currow * (G_Rel_GraphMargins[1] + G_Rel_GraphHeight) + G_Rel_GraphHeight],
        [G_Rel_GraphEdgeMargins[0] + curcol * (G_Rel_GraphMargins[0] + G_Rel_GraphWidth), G_Rel_GraphEdgeMargins[1] + currow * (G_Rel_GraphMargins[1] + G_Rel_GraphHeight)]
        ])

x_axis_positions = np.asarray([get_x_axis_coord(r,c) for r in range(G_GraphRows) for c in range(G_GraphCols)])
y_axis_positions = np.asarray([get_y_axis_coord(r,c) for r in range(G_GraphRows) for c in range(G_GraphCols)])
x_axis_positions_rel = np.asarray([get_x_axis_coord_rel(r,c) for r in range(G_GraphRows) for c in range(G_GraphCols)])
y_axis_positions_rel = np.asarray([get_y_axis_coord_rel(r,c) for r in range(G_GraphRows) for c in range(G_GraphCols)])

assert np.allclose(x_axis_positions_rel * [list(G_Pix_CanvasSize),list(G_Pix_CanvasSize)], x_axis_positions), "(Relative x-axis array * canvas size) should be equal to absolute x-axis array."
assert np.allclose(y_axis_positions_rel * [list(G_Pix_CanvasSize),list(G_Pix_CanvasSize)], y_axis_positions), "(Relative y-axis array * canvas size) should be equal to absolute y-axis array."




vertex = """
//attribute vec2 a_position;
attribute vec3 a_index;
attribute float a_random;
uniform vec2 u_edge_margin_offset;
uniform vec2 u_graph_margin;
uniform vec2 u_graph_size;
uniform float u_x_shift;

// Color.
attribute vec3 a_color;
varying vec4 v_color;
varying float v_do_clip;

void main (void)
{
    float x_shifted = 1.0 - ((1.0 - a_index.z) * u_x_shift );
    float x_pos = -1.0 + (u_edge_margin_offset.x + x_shifted*u_graph_size.x + a_index.x*(u_graph_margin.x + u_graph_size.x));
    float y_pos = -1.0 + (u_edge_margin_offset.y + (a_random)*u_graph_size.y + a_index.y*(u_graph_margin.y + u_graph_size.y));
    gl_Position = vec4(x_pos, y_pos, 0.0, 1.0);
    v_color = vec4(a_color, 1.);

    v_do_clip = 0.0;
    if    ( ( gl_Position.x < (-1 + u_edge_margin_offset.x + a_index.x*(u_graph_margin.x + u_graph_size.x)) ) ||
            ( gl_Position.x > (-1 + u_edge_margin_offset.x + a_index.x*(u_graph_margin.x + u_graph_size.x) + u_graph_size.x) ) ||
            ( gl_Position.y < (-1 + u_edge_margin_offset.y + a_index.y*(u_graph_margin.y + u_graph_size.y)) ) ||
            ( gl_Position.y > (-1 + u_edge_margin_offset.y + a_index.y*(u_graph_margin.y + u_graph_size.y) + u_graph_size.y) ) ||
            ( a_index.z == 1.0) || (a_index.z == 0.0) )
        v_do_clip = 1.0;



}
"""

fragment = """
varying vec4 v_color;
varying float v_do_clip;

void main() {
    gl_FragColor = v_color;

    // Clipping test.
    if ((v_do_clip == 1.0))
        discard;
}
"""




streams = list()
def select_stream():
    streams = resolve_stream('type', 'EEG')
    for i,s in enumerate(streams):
        print(i,s.name())
    stream_id = input("Input desired stream id: ")
    inlet = StreamInlet(streams[int(stream_id)])    
    return inlet
    
inlet = select_stream()
    
# Various signal amplitudes.
amplitudes = .1 + .2 * np.random.rand(G_NumChannels, 1).astype(np.float32)

# Generate the signals as a (m, n) array.
y = amplitudes * np.random.randn(G_NumChannels, G_MaximumBufferSize).astype(np.float32)


e = None
a = None
run1=True
ranan= np.c_[
                np.linspace(-1.0, +1.0, G_TotalShaders),
                np.tile(np.linspace(0.0, +1.0, G_MaximumBufferSize),G_NumChannels)].astype(np.float32)
class Canvas(app.Canvas):
    def __init__(self,app_to_use=None):
        app.Canvas.__init__(self, size=G_Pix_CanvasSize, title='Glyphs', keys='interactive', app=app_to_use)

        # Initialize starting parameters
        self.x_axis_len = 250. # in samples
        self.y_axis_height = 100. # in uV
        self.FS = 250.

        # Define axes
        self.x_axes = [visuals.AxisVisual(x_ax*[list(G_Pix_CanvasSize),list(G_Pix_CanvasSize)], (-1*self.x_axis_len/self.FS, 0.), (0., 1.), axis_label="S") for x_ax in x_axis_positions_rel]
        self.y_axes = [visuals.AxisVisual(y_ax*[list(G_Pix_CanvasSize),list(G_Pix_CanvasSize)], (0., self.y_axis_height), (-1., 0), axis_label="uV") for y_ax in y_axis_positions_rel]
        # Define shader program
        self.d = gloo.Program(vertex, fragment)
        self.d['a_color'] = G_ColorMap
        self.d['a_index'] = G_Rel_ShaderMapping.astype(np.float32)
        self.d['a_random'] = np.tile(np.linspace(0.0, +1.0, G_MaximumBufferSize),G_NumChannels).astype(np.float32)
        self.d['u_edge_margin_offset'] = np.asarray(G_Rel_GraphEdgeMargins) * 2.0
        self.d['u_graph_size'] = np.asarray(G_Rel_GraphSize) * 2.0
        self.d['u_graph_margin'] = np.asarray(G_Rel_GraphMargins) * 2.0
        self.d['u_x_shift'] = G_MaximumBufferSize / self.x_axis_len

        self._timer = app.Timer(1.0/250.0, connect=self.on_timer, start=True)

        gloo.set_state(clear_color='black', blend=True,
                       blend_func=('src_alpha', 'one_minus_src_alpha'))
#        self.show()
        self.printing = False
        
    def on_draw(self, event):
        gloo.clear('black')
        for x in self.x_axes:
            x.draw()
        for y in self.y_axes:
            y.draw()
        self.d.draw('line_strip')

    def on_mouse_wheel(self, event):
        dx = np.sign(event.delta[1]) * 100.
        self.x_axis_len = max([self.x_axis_len + dx, 25.])
        self.d['u_x_shift'] = G_MaximumBufferSize / self.x_axis_len
        for x in range(len(self.x_axes)):
            self.x_axes[x].domain = (-1*self.x_axis_len/self.FS, 0.)
        self.update()
        if np.sign(event.delta[1]) > 0:
            self.printing = True
        else:
            self.printing = False

    def on_resize(self, event):
        # Set canvas viewport and reconfigure visual transforms to match.
        vp = (0, 0, self.physical_size[0], self.physical_size[1])
        self.context.set_viewport(*vp)
        # Shift the axes on screen
        axis_shift_mat = [[self.physical_size[0], self.physical_size[1]],[self.physical_size[0],self.physical_size[1]]]
        for x in range(len(self.x_axes)):
            self.x_axes[x].pos = x_axis_positions_rel[x] * axis_shift_mat
            self.x_axes[x].transforms.configure(canvas=self, viewport=vp)
        for y in range(len(self.y_axes)):
            self.y_axes[y].pos = y_axis_positions_rel[y] * axis_shift_mat
            self.y_axes[y].transforms.configure(canvas=self, viewport=vp)

        self.update()

    def on_timer(self, event):
        (samples, timestamps) = inlet.pull_chunk(max_samples=250)

        # Check if we actually received any samples - pull_chunk doesn't block
        k = len(samples)
        if k == 0:
            return
        
        new_samples = np.transpose(samples)
        y[:, :-k] = y[:, k:]
        y[:, -k:] = new_samples

        
        # normalize
        yn = np.zeros_like(y)
#        print "YN", yn.shape
        for i in range(G_NumChannels):
            yn[i,:] = (y[i,:]/max(abs(y[i,:])*2.0)) + 0.5
            
        self.d['a_random'].set_data(yn.ravel().astype(np.float32))
        self.update()

import sys
from PySide.QtCore import *
from PySide.QtGui import * 

try:
    qt_app = QApplication([])
except RuntimeError:
    print "Qt Application Already Exists"
    pass
screen_resolution = qt_app.desktop().screenGeometry()
width, height = screen_resolution.width(), screen_resolution.height()
print width, height

Geo = QRect((width - G_Pix_CanvasWidth)/2.0, (height - G_Pix_CanvasHeight)/2.0, G_Pix_CanvasWidth, G_Pix_CanvasHeight)
Window = QWidget()
Window.setGeometry(Geo)
Window.setWindowTitle("Multiplot")
Layout = QGridLayout()
Window.setLayout(Layout)

c = Canvas()
c.measure_fps()

Layout.addWidget(c.native, 0, 0) 
Window.show()
sys.exit(qt_app.exec_())