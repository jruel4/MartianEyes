# -*- coding: utf-8 -*-
"""
Created on Sat Jul 15 23:46:01 2017

@author: marzipan
"""

import sys
import numpy as np
import time

from vispy import app, scene
from vispy import color as colour #generate color map
from pylsl import StreamInlet, resolve_stream

'''
generate color map
input: freqs, corresponding to x-val of every point on the graph
'''
def generate_color_map(freqs):
    # Here for reference (below)
    #  color.get_color_names()


    # This maps colors from (f1,f2]
    cmap_range = [
        [freqs[0]-1,3,'brown'],
        [3,6,'yellow'],
        [6,9,'orange'],
        [9,12,'red'],
        [12,16,'violet'],
        [16,20,'blue'],
        [20,24, 'turquoise'],
        [24,32, 'lightgreen'],
        [32,40, 'green'],
        [40,freqs[-1]+1, 'greenyellow']
    ]

    # Translate colormap to actual rbga values
    cmap = list()
    for freq in freqs:
        for freq_range in cmap_range:
            if (freq > freq_range[0]) and (freq <= freq_range[1]):
                cmap.append(colour.Color(freq_range[2]).rgba)
    return cmap

streams = list()
def select_stream():
    streams = resolve_stream()
    for i,s in enumerate(streams):
        print(i,s.name())
    stream_id = input("Input desired stream id: ")
    inlet = StreamInlet(streams[int(stream_id)])    
    return inlet

inlet = select_stream()



'''
PARAMETERS
'''

# corresponds to freq values of each point
#G_Freqs = np.linspace(0,125,G_LenSigPlot+1) #useful for fft periodo
G_Freqs = np.arange(8,14,1) # useful for wavelets
#G_Freqs = [10,15,20,25] # useful for wavelets

# rate at which the data was sampled (originally)
G_FS = 250 

#remove the first element of the periodogram - this is the DC component
G_RemoveDC = False

#remove the second half of the periodogram (mirror)
G_RemoveMirror = False 

#set to 1 if no MA is desired
G_MovingAverageLen = 1000


# the number of channels we are receiving
G_NChanIn = 8

# This is the number of channels to display
G_NChanPlot = 7

# rows x columns, must match up with G_NChanPlot
rows = 7
cols = 1

# dynamically get input length
sample_tst, _ts = inlet.pull_sample()
G_LengthOfInput = len(sample_tst)
G_LenSigIn = G_LengthOfInput/G_NChanIn

# adjust plotting length if removing components
G_LenSigPlot = G_LenSigIn
if G_RemoveMirror:
    G_LenSigPlot=G_LenSigPlot/2
if G_RemoveDC:
    G_LenSigPlot=G_LenSigPlot-1

# array below represents x/y combos for each point
pos = np.zeros((G_NChanPlot, G_LenSigPlot, 2), dtype=np.float32)
pos[:,:, 0] = G_Freqs # x vals (freqs)

color = generate_color_map(G_Freqs)




# TODO
once = True
buflen = 5000
conv2uv = False
conv2uvfromv = True

i2v = ( (4.5 / (2**23 - 1)) / 24)

G_MABuffer = np.zeros([buflen,G_NChanIn,G_LenSigIn])
last_upd = 0
# END TODO




'''
Asserts / checks
'''

assert G_MovingAverageLen >= 1
if G_LengthOfInput % G_NChanIn:
    raise RuntimeError("Number of expected channels and length of input do not match, G_NChanIn: ", G_NChanIn, " len(input): ", G_LengthOfInput)

# Alert user if DC / mirror may have already been removed
if (G_LengthOfInput/G_NChanIn) % 2:
    print "Length of periodogram is odd, len: ", G_LengthOfInput/G_NChanIn, ", may not need to remove mirror or DC component"

assert len(G_Freqs) == G_LenSigPlot


canvas = scene.SceneCanvas(keys=None, show=False)
grid = canvas.central_widget.add_grid(spacing=0,margin=10,padding=10)
lines = list()
viewboxes = list()
for r in range(rows):
    for c in range(cols):
        viewboxes.append(grid.add_view(row=r*2, col=c, camera='panzoom'))
        
        if r*cols + c < G_NChanPlot:
            # add some axes
            x_axis = scene.AxisWidget(orientation='bottom', axis_label="Hz")
            x_axis.stretch = (1, 0.1)
            xax = x_axis
            grid.add_widget(x_axis, row=1+r*2, col=c,col_span=1, row_span=1)
            x_axis.link_view(viewboxes[c + r*cols])
            y_axis = scene.AxisWidget(orientation='left', axis_label="uV")
            y_axis.stretch = (0.1, 1)
            grid.add_widget(y_axis, row=0+r*2, col=c)
            y_axis.link_view(viewboxes[c + r*cols])
        
            # add a line plot inside the viewbox
            lines.append(scene.Line(pos[c + r*cols,:,:], color, parent=viewboxes[c + r*cols].scene))

'''

'''
eva=list()
def update(ev):
    global pos, color, lines,inlet,conv2uv,once,viewboxes,G_MABuffer,last_upd,i2v,eva
    eva.append(ev)
    # Samples is a #samples x nchan*nfreqs
    (samples, timestamps) = inlet.pull_chunk(max_samples=len(G_MABuffer)-1)

    # Check if we actually received any samples - pull_chunk doesn't block
    k = len(samples)
    if k == 0:
        return
    
    if once: print "Samples, ", np.shape(samples)

    if G_MovingAverageLen > 1:
        
        samples_tmp = np.reshape(samples,[-1,G_NChanIn, G_LenSigIn])
        
        for ch in range(G_NChanIn):
            #generate T/F values for each sample based on whether or not it contains any negatives
            do_keep = samples_tmp[:,ch,:].min(axis=1) >= 0 

            #use above value to nix any samples that have negatives
            samples_to_append = samples_tmp[do_keep,ch,:]
            
            #if all samples were negative then skip updating the MA
            k = len(samples_to_append)
            if k > 0:
                # Shift the moving average buffer
                G_MABuffer[:-k,ch,:] = G_MABuffer[k:,ch,:]
                # Update the newest values
                G_MABuffer[-k:,ch,:] = samples_to_append
        
        if once: print "(MA)New samples, shape: ", np.shape(G_MABuffer[-G_MovingAverageLen:, :, :] / float(G_MovingAverageLen))
        new_samples = np.sum(G_MABuffer[-G_MovingAverageLen:, :, :],0) / float(G_MovingAverageLen)

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
        sc_pos[:,:,1] *= i2v
    if conv2uvfromv:
        sc_pos[:,:,1] *= 1e6

    # Update lines with new data
    for i in range(len(lines)):
        lines[i].set_data(pos=sc_pos[i,:,:], color=color)

    # Update x/y axis
    if (time.time() - last_upd) > 1.0:
        for i in range(len(viewboxes)):
            viewboxes[i].camera.set_range(x=(G_Freqs[0], G_Freqs[-1]), y=(0, max(sc_pos[i,:,1]) ) )
        last_upd = time.time()
    
    # Stop printing
    once = False

if __name__ == '__main__' and sys.flags.interactive == 0:
    app.run()
    
    timer = app.Timer(interval=0.01 ,iterations=-1)
    timer.connect(update)
    timer.start(0)
    
    canvas.show()