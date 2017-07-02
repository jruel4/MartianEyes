

import numpy as np
from vispy import plot as vp
import time
from threading import Thread

class SinglePlotFigure:

    def __init__(self, inlet):
        self.inlet = inlet
        self.fig = vp.Fig(size=(800, 800), show=False)
        self.x = np.linspace(0, 10, 20)
        self.xn = self.x.copy()
        self.y = np.ones((8,600)) * 8.1
        self.y[:,0]=-1
        self.colors = [(0.8, 0, 0, 1),
                  (0.8, 0, 0.8, 1),
                  (0, 0, 1.0, 1),
                  (0, 0.7, 0, 1), 
                  (0.18, 0, 0, 1),
                  (0.18, 0, 0.8, 1),
                  (0.1, 0, 1.0, 1),
                  (0.1, 0.7, 0, 1),]                  
        self.lines = []
        for i in range(1):
            self.lines += [self.fig[0, 0].plot(self.y[i,:], color=self.colors[i])]
        self.grid = vp.visuals.GridLines(color=(0, 0, 0, 0.5))
        self.grid.set_gl_state('translucent')
        self.fig[0, 0].view.add(self.grid)
        self.idx = 0
        self.begin = time.time()
        
    def update_plot(self, event):
        
        if self.idx==0: self.begin = time.time()
        self.idx+=1
        if self.idx %100 == 0:
    
            pass
       
        try:
            
            for i,line in enumerate(self.lines):
                line.set_data(self.y[i,:]+i, color=self.colors[i])
    
            self.fig.update()
    
            
        except RuntimeError as err:
            if 'EventEmitter loop detected' in err.args[0]: #TODO handle this correctly
                pass
    
    def update_data(self):

        while True:
            #time.sleep(0) #yield 
            sample, timestamp = self.inlet.pull_sample()
            #print(sample[0])
            new_samples = np.asarray(sample)
            k = 1
            self.y[:, :-k] = self.y[:, k:]
            self.y[:, -k:] = new_samples[:,None]     
        
        
    
    #==============================================================================
    # timer = app.Timer()
    # timer.connect(update_plot)
    # timer.start(1.0/200)
    #==============================================================================
    
    def run(self, timer):
        timer.timeout.connect(self.update_plot)
        timer.start(1.0/200)
        self.fig.show()
        thread = Thread(target=self.update_data)
        thread.start()

    
