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



# Parameters
G_FS = 250 # rate at which the data was sampled (originally)
G_RemoveDC = True #remove the first element of the periodogram - this is the DC component
G_RemoveMirror = True #remove the second half of the spectrogram (mirror)
G_MovingAverageLen = 1

G_Freqs = [0.5,125]

# This is the number of channels we are receiving
G_NChanIn = 8

# This is the number of channels to display
G_NChanPlot = 2
rows = 2
cols = 1

# dynamically get length
sample_tst, _ts = inlet.pull_sample()
G_LengthOfInput = len(sample_tst)


# Calculate the frequencies
#G_Freqs = np.linspace(0, G_FS, G_LengthOfInput)

# Moving average length must be greater than 1
assert G_MovingAverageLen >= 1

# Length of input should be evenly divisible by number of channels we expect
if G_LengthOfInput % G_NChanIn:
    raise RuntimeError("Number of expected channels and length of input do not match, G_NChanIn: ", G_NChanIn, " len(input): ", G_LengthOfInput)

# Alert user if DC / mirror may have already been removed
if (G_LengthOfInput/G_NChanIn) % 2:
    print "Length of periodogram is odd, len: ", G_LengthOfInput/G_NChanIn, ", may not need to remove mirror or DC component"

# vertex positions of data to draw
G_LenSigIn = G_LengthOfInput/G_NChanIn

G_LenSigPlot = G_LenSigIn
if G_RemoveMirror:
    G_LenSigPlot=G_LenSigPlot/2
if G_RemoveDC:
    G_LenSigPlot=G_LenSigPlot-1

pos = np.zeros((G_NChanPlot, G_LenSigPlot, 2), dtype=np.float32)
x_lim = [G_Freqs[0], G_Freqs[1]]
y_lim = [-2., 2.]
pos[:,:, 0] = np.linspace(x_lim[0], x_lim[1], G_LenSigPlot)
pos[:,:, 1] = np.random.normal(size=G_LenSigPlot)

# Here for reference (below)
#  color.get_color_names()

from vispy import color as colour
# This maps colors from (f1,f2]
color_map = [
[G_Freqs[0]-1,3,'brown'],
[3,6,'yellow'],
[6,9,'orange'],
[9,12,'red'],
[12,16,'violet'],
[16,20,'blue'],
[20,24, 'turquoise'],
[24,32, 'lightgreen'],
[32,40, 'green'],
[40,G_Freqs[1]+1, 'greenyellow']
]

# Translate colormap to actual rbga values
color = list()
for freq in np.linspace(G_Freqs[0], G_Freqs[1], G_LenSigPlot):
    for freq_range in color_map:
        if (freq > freq_range[0]) and (freq <= freq_range[1]):
            color.append(colour.Color(freq_range[2]).rgba)

canvas = scene.SceneCanvas(keys=None, show=False)
grid = canvas.central_widget.add_grid(spacing=0)

lines = list()
viewboxes = list()
for r in range(rows):
    for c in range(cols):
        viewboxes.append(grid.add_view(row=r*2, col=c, camera='panzoom'))
        
        if r*cols + c < G_NChanPlot:
            # add some axes
            x_axis = scene.AxisWidget(orientation='bottom', domain=G_Freqs, axis_label="Hz")
            x_axis.stretch = (1, 0.1)
            xax = x_axis
            grid.add_widget(x_axis, row=1+r*2, col=c,col_span=1, row_span=1)
            x_axis.link_view(viewboxes[c + r*cols])
            y_axis = scene.AxisWidget(orientation='right')
            y_axis.stretch = (0.1, 1)
            grid.add_widget(y_axis, row=0+r*2, col=c)
            y_axis.link_view(viewboxes[c + r*cols])
        
            # add a line plot inside the viewbox
            lines.append(scene.Line(pos[c + r*cols,:,:], color, parent=viewboxes[c + r*cols].scene))


once = True
buflen = 250
conv2uv = False

def scale_to_volts(raw, gain = 24, vref = 4.5):
     return  raw * ( (vref / (2**23 - 1)) / gain)

G_MABuffer = np.zeros([buflen,G_NChanIn,G_LenSigIn])

def update(ev):
    global pos, color, lines,inlet,conv2uv,once,viewboxes,G_MABuffer
    
    # Samples is a #samples x nchan*nfreqs
    (samples, timestamps) = inlet.pull_chunk(max_samples=len(G_MABuffer)-1)

    # Check if we actually received any samples - pull_chunk doesn't block
    k = len(samples)
    if k == 0:
        return
    
    if once: print "Samples, ", np.shape(samples)

    if G_MovingAverageLen > 1:
        # Shift the moving average buffer
        G_MABuffer[:-k,:,:] = G_MABuffer[k:,:,:]
        G_MABuffer[-k:,:,:] = np.reshape(samples,[-1,G_NChanIn, G_LenSigIn])
        
        if once: print "(MA)New samples, shape: ", np.shape(G_MABuffer[-G_MovingAverageLen:, :, :] / float(len(G_MABuffer)))
        new_samples = np.sum(G_MABuffer[-G_MovingAverageLen:, :, :],0) / float(len(G_MABuffer))

    else:
        # Discard all but the most recent sample
        new_samples = np.asarray(samples)[-1,:]
        if once: print "New samples, discarded all but current sample: ", new_samples.shape
    
        # Reshape to match 
        new_samples = np.reshape(new_samples,[G_NChanIn,G_LenSigIn])
        if once: print "New samples, reshaped: ", new_samples.shape
        if once: print "New samples, unused channels cleaved: ", new_samples[range(G_NChanPlot),:].shape
    
    # Remove mirror and remove DC
    if G_RemoveMirror:
        if once: print "New samples, mirror cleaved: ", new_samples[:,:G_LenSigIn/2].shape        
        new_samples = new_samples[:,:G_LenSigIn/2]
    if G_RemoveDC:
        if once: print "New samples, DC cleaved: ", new_samples[:,1:].shape
        new_samples = new_samples[:,1:]
        

    if once: print "Pos[:,:,1], : ", pos[:,:,1].shape
    pos[:,:,1] = new_samples[range(G_NChanPlot),:]


    sc_pos = pos.copy()
    if conv2uv:        
        sc_pos[:,:,1] = scale_to_volts(sc_pos[:,:,1]) * 1000000.0

#    color = np.roll(color, 1, axis=0)
    for i in range(len(lines)):
        lines[i].set_data(pos=sc_pos[i,:,:], color=color)


    if once:
        for i in viewboxes:
            i.camera.set_range()
    
    # Stop printing
    once = False

if __name__ == '__main__' and sys.flags.interactive == 0:
    app.run()
    
    timer = app.Timer(iterations=50000)
    timer.connect(update)
    timer.start(0)
    
    canvas.show()