# -*- coding: utf-8 -*-
"""
Created on Fri Jul 14 23:54:29 2017

@author: marzipan
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 09:45:43 2017

@author: marzipan
"""

"""
Multiple real-time digital signals with GLSL-based clipping.
"""
from vispy import app, gloo, visuals
import numpy as np



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
    gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
}
"""
#program = gloo.Program(vertex, fragment)

#program['a_position'] = np.c_[
#        np.linspace(-1.0, +1.0, 1000),
#        np.random.uniform(-0.5, +0.5, 1000)].astype(np.float32)



# size of canvas and graph
canvas_size = (800, 600)
graph_size = (500, 500)

# vertex positions of data to draw
N = 30

margin_x = (canvas_size[0]-graph_size[0]) / 2.
margin_y = (canvas_size[1]-graph_size[1]) / 2.

pos_xax = np.array([[margin_x, canvas_size[1]-margin_y],
                   [canvas_size[0]-margin_x, canvas_size[1]-margin_y]])

class Canvas(app.Canvas):
    def __init__(self):
        app.Canvas.__init__(self, size=canvas_size, title='Glyphs', keys='interactive',show=True)
        self.axis_start = 0.0
        self.axis_end = 1.0
        self.axis1 = visuals.AxisVisual(pos_xax, (0, 100), (0., 1.))
        
    
    def on_draw(self, event):
        gloo.clear(color='black')
        self.axis1.draw()

    def on_mouse_wheel(self, event):
        print "Event: ", event
#        gloo.set_viewport(0, 0, *self.physical_size)
#        self.font_size += 0.1 if event.delta[1] > 0 else 0.8
#        self.apply_zoom()

    def on_resize(self, event):
        # Set canvas viewport and reconfigure visual transforms to match.
        vp = (0, 0, self.physical_size[0], self.physical_size[1])
        self.context.set_viewport(*vp)
        self.axis1.transforms.configure(canvas=self, viewport=vp)
#        self.axis_y.transforms.configure(canvas=self, viewport=vp)
#        self.line.transforms.configure(canvas=self, viewport=vp)


'''
class Canvas(app.Canvas):
    def __init__(self):
        app.Canvas.__init__(self, title='Glyphs', keys='interactive')
        self.font_size = 48.
        self.text = visuals.TextVisual('', bold=True)
        self.apply_zoom()

    def on_draw(self, event):
        gloo.clear(color='white')
        gloo.set_viewport(0, 0, *self.physical_size)
        self.text.draw()

    def on_mouse_wheel(self, event):
        """Use the mouse wheel to zoom."""
        self.font_size *= 1.25 if event.delta[1] > 0 else 0.8
        self.font_size = max(min(self.font_size, 160.), 6.)
        self.apply_zoom()

    def on_resize(self, event):
        # Set canvas viewport and reconfigure visual transforms to match.
        vp = (0, 0, self.physical_size[0], self.physical_size[1])
        self.context.set_viewport(*vp)
        self.text.transforms.configure(canvas=self, viewport=vp)
        self.apply_zoom()

    def apply_zoom(self):
        self.text.text = '%s pt' % round(self.font_size, 1)
        self.text.font_size = self.font_size
        self.text.pos = self.size[0] // 2, self.size[1] // 2
        self.update()

if __name__ == '__main__':
    c1 = Canvas()
    c1.show()
    c1.app.run()    
'''
    
c = Canvas()  
    
#c.show()

app.run()