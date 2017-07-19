# -*- coding: utf-8 -*-
"""
Created on Sun Mar 19 03:22:21 2017

@author: marzipan
"""

from threading import Thread
import mne
import numpy as np
import time
import matplotlib.pyplot as plt

fig = plt.figure()
ax = fig.add_subplot(111)

data = np.asarray([1, 1, 1, 1, -1])
data_pos = np.asarray([[0,0], [1,1], [0,1], [1,0], [0.7,0.5]])
ln,qs,Zi = mne.viz.plot_topomap_mod(data,data_pos,axes=ax)

def animation_loop():
    for i,j in [(i,j) for i in range(64) for j in range(64)]:
        Zi[i,j] = 10
        ln.set_data(Zi)
        time.sleep(1.0/60.0)
        fig.canvas.draw()

thread = Thread(target = animation_loop)
thread.start()








