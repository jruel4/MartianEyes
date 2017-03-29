# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 09:45:43 2017

@author: marzipan
"""

"""
Multiple real-time digital signals with GLSL-based clipping.
"""

from vispy import gloo
from vispy import app
import numpy as np
import math
from PySide.QtCore import *
from PySide.QtGui import * 
import sys
from pylsl import StreamInlet, resolve_stream
from scaling import scale_p1_m1

try:
    if __name__ == '__main__':
        qt_app = QApplication(sys.argv)
except Exception as e: # could fail for reasons other than already exists... 
    print(e)

# Number of cols and rows in the table.
nrows = 8
ncols = 1

# Number of signals.
m = nrows*ncols

# Number of samples per signal.
n = 1000
    
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
amplitudes = .1 + .2 * np.random.rand(m, 1).astype(np.float32)

# Generate the signals as a (m, n) array.
y = amplitudes * np.random.randn(m, n).astype(np.float32)

# Color of each vertex (TODO: make it more efficient by using a GLSL-based
# color map and the index).
color = np.repeat(np.random.uniform(size=(m, 3), low=.5, high=.9),
                  n, axis=0).astype(np.float32)

# Signal 2D index of each vertex (row and col) and x-index (sample index
# within each signal).
index = np.c_[np.repeat(np.repeat(np.arange(ncols), nrows), n),
              np.repeat(np.tile(np.arange(nrows), ncols), n),
              np.tile(np.arange(n), m)].astype(np.float32)

VERT_SHADER = """
#version 120

// y coordinate of the position.
attribute float a_position;

// row, col, and time index.
attribute vec3 a_index;
varying vec3 v_index;

// 2D scaling factor (zooming).
uniform vec2 u_scale;

// Size of the table.
uniform vec2 u_size;

// Number of samples per signal.
uniform float u_n;

// Color.
attribute vec3 a_color;
varying vec4 v_color;

// Varying variables used for clipping in the fragment shader.
varying vec2 v_position;
varying vec4 v_ab;

void main() {
    float nrows = u_size.x;
    float ncols = u_size.y;

    // Compute the x coordinate from the time index.
    float x = -1 + 2*a_index.z / (u_n-1);
    vec2 position = vec2(x - (1 - 1 / u_scale.x), a_position);

    // Find the affine transformation for the subplots.
    vec2 a = vec2(1./ncols, 1./nrows)*.9;
    vec2 b = vec2(-1 + 2*(a_index.x+.5) / ncols,
                  -1 + 2*(a_index.y+.5) / nrows);
    // Apply the static subplot transformation + scaling.
    gl_Position = vec4(a*u_scale*position+b, 0.0, 1.0);

    v_color = vec4(a_color, 1.);
    v_index = a_index;

    // For clipping test in the fragment shader.
    v_position = gl_Position.xy;
    v_ab = vec4(a, b);
}
"""

FRAG_SHADER = """
#version 120

varying vec4 v_color;
varying vec3 v_index;

varying vec2 v_position;
varying vec4 v_ab;

void main() {
    gl_FragColor = v_color;

    // Discard the fragments between the signals (emulate glMultiDrawArrays).
    if ((fract(v_index.x) > 0.) || (fract(v_index.y) > 0.))
        discard;

    // Clipping test.
    bool apply_clipping = false;
    vec2 test = abs((v_position.xy-v_ab.zw)/v_ab.xy);
    if (((test.x > 1) || (test.y > 1)) && apply_clipping)
        discard;
}
"""


class Canvas(app.Canvas):
    def __init__(self):
        app.Canvas.__init__(self, title='Use your wheel to zoom!',
                            keys='interactive', app="PySide")
        self.program = gloo.Program(VERT_SHADER, FRAG_SHADER)
        self.program['a_position'] = y.reshape(-1, 1)
        self.program['a_color'] = color
        self.program['a_index'] = index
        self.program['u_scale'] = (1., 1.)
        self.program['u_size'] = (nrows, ncols)
        self.program['u_n'] = n

        gloo.set_viewport(0, 0, *self.physical_size)

        #TODO change positional timer argument back to 'auto' and multiple handle sample pulling logic
        self._timer = app.Timer(1.0/250.0, connect=self.on_timer, start=True)

        gloo.set_state(clear_color='black', blend=True,
                       blend_func=('src_alpha', 'one_minus_src_alpha'))

        self.show()

    def on_resize(self, event):
        gloo.set_viewport(0, 0, *event.physical_size)

    def on_mouse_wheel(self, event):
        dx = np.sign(event.delta[1]) * .05
        scale_x, scale_y = self.program['u_scale']
        scale_x_new, scale_y_new = (scale_x * math.exp(2.5*dx),
                                    scale_y * math.exp(0.0*dx))
        self.program['u_scale'] = (max(1, scale_x_new), max(1, scale_y_new))
        self.update()
        
    def on_key_press(self, event):
        if event.key in ['Left', 'Right', 'Up', 'Down']:
            if event.key == 'Right':
                dx = 0
            elif event.key == 'Up':
                dx = 0.2
            elif event.key == 'Down':
                dx = -0.2
            else:
                dx = 0
            scale_x, scale_y = self.program['u_scale']
            scale_x_new, scale_y_new = (scale_x, scale_y * math.exp(1.0*dx))
            self.program['u_scale'] = (max(1, scale_x_new), max(1, scale_y_new))
            self.update()

    def on_timer(self, event):
        sample, timestamp = inlet.pull_sample()
        k = 1
        new_samples = np.asarray(sample)
        y[:, :-k] = y[:, k:]
        #y[:, -k:] = amplitudes * np.random.randn(m, k)
        y[:, -k:] = new_samples[:,None]
        
        # normalize
        yn = np.zeros_like(y)
        for i in range(8):
            yn[i,:] = scale_p1_m1(y[i,:])
    
        self.program['a_position'].set_data(yn.ravel().astype(np.float32))
        self.update()
        
    def on_draw(self, event):
        gloo.clear()
        self.program.draw('line_strip')

if __name__ == '__main__':
    c = Canvas()
    try:
        qt_app.exec_()
    except NameError as e:
        print(e)




