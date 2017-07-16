# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 01:00:56 2017

@author: marzipan
"""

import time
import numpy as np
from pylsl import  StreamInlet, resolve_stream, StreamInfo, StreamOutlet
from threading import Thread

def create_test_source(freq=10, sps=250):
    '''
    create fake lsl stream of source data
    '''
    assert freq < (sps/2), "frequence must be less than nyquist"
    stream_name = "Test_Signal_"+str(freq)+"_Hz_"
    stream_id = stream_name + time.strftime("_%d_%m_%Y_%H_%M_%S_")
    info = StreamInfo(stream_name, 'EEG', 8, 250, 'float32', stream_id)
    outlet = StreamOutlet(info)
    delay = 1.0/sps
    def _target():
        idx = 0
        mode = True
        while True:
            time.sleep(delay)
            idx += 1
            if idx % 2000 == 0:
                mode = not mode
            if mode:
               new_val = np.sin(2*np.pi*freq*(idx*delay))
            else:
                new_val = np.sin(2*np.pi*freq*2*(idx*delay))
            outlet.push_sample([new_val for i in range(8)])
    _thread = Thread(target=_target)
    _thread.start()
    
def create_multi_ch_test_source(freqs=[i for i in range(2,10)], sps=250):
    '''
    create fake lsl stream of source data
    '''
    assert len(freqs) == 8, "freqs array must be length 8"
    stream_name = "Test_Signal_"+str(freqs[0])+"_Multi_Hz_"
    stream_id = stream_name + time.strftime("_%d_%m_%Y_%H_%M_%S_")
    info = StreamInfo(stream_name, 'EEG', 8, 250, 'float32', stream_id)
    outlet = StreamOutlet(info)
    delay = 1.0/sps
    def _target():
        idx = 0
        while True:
            time.sleep(delay)
            idx += 1
            
            new_vals = [np.sin(2*np.pi*freq*(idx*delay)) for freq in freqs]

            outlet.push_sample(new_vals)
    _thread = Thread(target=_target)
    _thread.start()
    
def create_noisy_test_source(freq=10, noise_freq=60, sps=250):
    '''
    create fake lsl stream of source data
    '''
    assert freq < (sps/2), "frequence must be less than nquist"
    stream_name = "Test_Signal_"+str(freq)+"_Hz_"
    stream_id = stream_name + time.strftime("_%d_%m_%Y_%H_%M_%S_")
    info = StreamInfo(stream_name, 'EEG', 8, 250, 'float32', stream_id)
    outlet = StreamOutlet(info)
    delay = 1.0/sps
    def _target():
        idx = 0
        while True:
            time.sleep(delay)
            idx += 1
            new_val = np.sin(2*np.pi*freq*(idx*delay)) + np.sin(2*np.pi*noise_freq*(idx*delay))
            outlet.push_sample([new_val for i in range(8)])
    _thread = Thread(target=_target)
    _thread.start()
            
def select_stream():
    streams = resolve_stream('type', 'EEG')
    for i,s in enumerate(streams):
        print(i,s.name())
    stream_id = input("Input desired stream id: ")
    inlet = StreamInlet(streams[int(stream_id)])    
    return inlet

def get_stream_fps():
    inlet = select_stream()
    begin = time.time()
    idx = 0
    try:
        while True:
            idx += 1
            inlet.pull_sample()
            if idx % 60 == 0:
                print("fps: ",idx/(time.time()-begin))
    except KeyboardInterrupt:
        pass
    
def create_fake_eeg(sps=250, nchan=8,name=""):
    '''
    create fake eeg strea - for testing spectrographic 'zoom' feature
    requires some high amplitude noise as well as broad band noise for realism
    '''
    freqs = list(range(10,10+nchan))
    stream_name = name + "_Fake_EEG_"
    stream_id = stream_name + time.strftime("_%d_%m_%Y_%H_%M_%S_")
    info = StreamInfo(stream_name, 'EEG', nchan, 250, 'float32', stream_id)
    outlet = StreamOutlet(info)
    delay = 1.0/sps
    def _target():
        idx = 0
        while True:
            time.sleep(delay)
            idx += 1
            line_noise = 10.0*np.sin(2*np.pi*60*(idx*delay))
            white_noise = 0.7*np.random.rand()
            new_vals = [white_noise + line_noise + 1.2*np.sin(2*np.pi*freq*(idx*delay)) for freq in freqs]

            outlet.push_sample(new_vals)
    _thread = Thread(target=_target)
    _thread.start()
    return _thread

def create_fake_spectro(name="",sps=10.,freqs=250, peaks=[14,15,18,60]):
    '''
    create fake spectrogram lsl output (testing purposes)
    '''
    stream_name = name + "_Fake_EEG_Spect_"
    stream_id = stream_name + time.strftime("_%d_%m_%Y_%H_%M_%S_")
    info = StreamInfo(stream_name, 'EEG', freqs, sps, 'float32', stream_id)
    outlet = StreamOutlet(info)
    delay = 1.0/sps
    
    # Generate fake sine w/ target peaks
    main_sin = np.zeros(freqs*2)
    for peak in peaks:
        main_sin += [np.sin(2.0*np.pi*(x/250.0)*peak) for x in range(freqs*2)]
    
    def _target():
        idx = 0
        while True:
            time.sleep(delay)
            idx += 1
            tmp_sig = main_sin + 0.7*np.random.rand(freqs*2)
            fft = np.abs(np.fft.fft(tmp_sig))[:(freqs)]
            if idx % 100:
                print "FFT: ", fft.shape
            outlet.push_sample(fft)
    _thread = Thread(target=_target)
    _thread.start()
    return _thread


def create_fake_eeg_increasing_beta(sps=250, nchan=8):
    '''
    create fake eeg strea - for testing spectrographic 'zoom' feature
    requires some high amplitude noise as well as broad band noise for realism
    '''
    freqs = list(range(10,10+nchan))
    stream_name = "Fake_EEG_BetaCycle_"
    stream_id = stream_name + time.strftime("_%d_%m_%Y_%H_%M_%S_")
    info = StreamInfo(stream_name, 'EEG', nchan, 250, 'float32', stream_id)
    outlet = StreamOutlet(info)
    delay = 1.0/sps
    def _target():
        idx = 0
        while True:
            time.sleep(delay)
            idx += 1
            line_noise = 10.0*np.sin(2*np.pi*60*(idx*delay))
            white_noise = 0.7*np.random.rand()
            beta = ((idx % sps*10.) / sps*2.5) *np.sin(2*np.pi*22*(idx*delay)) #cycle every 10 seconds between 0 and 4
            new_vals = [white_noise + line_noise + 1.2*np.sin(2*np.pi*freq*(idx*delay)) + beta for freq in freqs]

            outlet.push_sample(new_vals)
    _thread = Thread(target=_target)
    _thread.start()
    return _thread


def create_fake_audio(sps=250):
    '''
    create fake audio input
    '''
    stream_name = "Fake_Audio_"
    stream_id = stream_name + time.strftime("_%d_%m_%Y_%H_%M_%S_")
    info = StreamInfo(stream_name, 'Audio', 4, sps, 'float32', stream_id)
    outlet = StreamOutlet(info)
    delay = 1.0/sps
    def _target():
        idx = 0
        while True:
            time.sleep(delay)
            outlet.push_sample([np.random.randint(1,5) for i in range(4)])
            outlet.push_sample(new_vals)
    _thread = Thread(target=_target)
    _thread.start()
    return _thread



class tuneable_scalar(object):
    def __init__(self, _val=1.0):
        self.val = _val
        
    def _target(self):
        idx = 0
        while True:
            time.sleep(self.delay)
            idx += 1
            new_vals = [self.val for i in range(8)]
            self.outlet.push_sample(new_vals)
        
    def run(self,sps=50):
        stream_name = "Tunable_scalar"
        stream_id = stream_name + time.strftime("_%d_%m_%Y_%H_%M_%S_")
        info = StreamInfo(stream_name, 'EEG', 8, 50, 'float32', stream_id)
        self.outlet = StreamOutlet(info)
        self.delay = 1.0/sps
        _thread = Thread(target=self._target)
        _thread.start()
        
    def tune(self,_val):
        self.val = _val

        



