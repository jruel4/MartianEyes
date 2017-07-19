# -*- coding: utf-8 -*-
"""
Created on Wed Jul 19 07:50:00 2017

@author: marzipan
"""

from PyQt4 import QtGui
import sys
import numpy as np

from pyqtgraph.Qt import QtCore
import pyqtgraph as pg

from pylsl import resolve_stream, StreamInlet

import GUIMain
from Utils.lsl_utils import select_stream

class GUITest(QtGui.QMainWindow, GUIMain.Ui_MainWindow):
    def __init__(self, parent=None):
        super(GUITest, self).__init__(parent)
        self.setupUi(self)

        self.pbGraphInGUI.clicked.connect(self.graphInGUI)
        self.pbLaunchGraphs.clicked.connect(self.launchGraphs)
        self.pbLaunchPeriodo.clicked.connect(self.launchPeriodo)

        # Refresh stream info whenever new stream is chosen
        self.cbLSLStream.currentIndexChanged.connect(self._update_stream_info)
        self.cbChBeg.currentIndexChanged.connect(self._update_ch_idx)
        self.cbChEnd.currentIndexChanged.connect(self._update_ch_idx)
        self.cbColumns.currentIndexChanged.connect(self._update_rc_idx)
        self.cbRows.currentIndexChanged.connect(self._update_rc_idx)
        
        # Parameters
        self.FS = 250.
        self.graphBufSize = 1000
 
        ###
        # Add GUI defaults      
        ###

        self.graphWindow = None
        self.periodoWindow = None
        self.timer = None
        self.periodoTimer = None
        
        self.nRow = None
        self.nCol = None
        self.nChan = None
        self.chanIDX = None
        
        self._reset_channel_count() # MUST COME FIRST
        self._reset_channel_select()
        self._reset_freq_band()
        self._reset_rc_select()
        self._reset_lsl_stream_select()

    def _graph_upd(self):        
        # Samples is (samples, nchan)
        (samples, timestamps) = self.inlet.pull_chunk(max_samples=self.graphBufSize-1)
    
        # Check if we actually received any samples - pull_chunk doesn't block
        k = len(samples)
        if k == 0:
            return
    
        # new_samples shape: (nchan, nsamples)
        new_samples = np.transpose(samples)

        # shift buffer
        self.graphBuf[self.chanIDX, :-k] = self.graphBuf[self.chanIDX, k:]
        self.graphBuf[self.chanIDX, -k:] = new_samples[self.chanIDX,:]
        
        # update graph
        for i in self.chanIDX:
            self.graphLineData[i].setData(self.graphBuf[i,:])


    def _periodo_upd(self):
        # Samples is a #samples x nchan*nfreqs
        (samples, timestamps) = self.inlet.pull_chunk(max_samples=self.periodoLen-1)
#        (samples, timestamps) = self.inlet.pull_sample()

        # Check if we actually received any samples - pull_chunk doesn't block
        k = len(samples)
        if k == 0:
            return
        
        # reshape to [nsamples, nchan, nfreqs] and cleave all but the latest sample
        self.periodoBuf = np.reshape(samples,[-1,self.nChan, self.periodoLen])[-1,:,:]
        for i in self.chanIDX:
            self.periodoLineData[i].setData(self.periodoBuf[i,:])

    def _reset_channel_select(self):
        self.cbChBeg.clear()
        self.cbChEnd.clear()
        self.cbChBeg.addItems([str(i+1) for i in range(self.nChan)])
        self.cbChEnd.addItems([str(i+1) for i in range(self.nChan)])
        self.cbChEnd.setCurrentIndex(self.nChan - 1)
        self._update_ch_idx(0)
        
    def _reset_rc_select(self):
        self.cbRows.clear()
        self.cbColumns.clear()
        self.cbRows.addItems([str(i+1) for i in range(self.nChan)])
        self.cbColumns.addItems([str(i+1) for i in range(self.nChan)])
        self.cbRows.setCurrentIndex(self.nChan - 1)
        self._update_rc_idx(0)

    def _reset_lsl_stream_select(self):
        self.cbLSLStream.clear()
        streams = resolve_stream()
        for s in streams:
            self.cbLSLStream.addItem(s.name(),s)
        self._update_stream_info(self.cbLSLStream.currentIndex())
            
    def _reset_freq_band(self):
        self.dsbFStart.setValue(0.0)
        self.dsbFEnd.setValue(125.0)
    
    def _reset_channel_count(self):
        self.sbTotalChan.setValue(8)
        self.sbTotalSubchannels.setValue(0)
        self.nChan = 8

    def _update_ch_idx(self,idx):
        b = int(self.cbChBeg.itemText(self.cbChBeg.currentIndex()))-1
        e = int(self.cbChEnd.itemText(self.cbChEnd.currentIndex()))-1
        self.chanIDX = range(b, max([b,e])+1)

    def _update_rc_idx(self,idx):
        self.nRow = int(self.cbRows.itemText(self.cbRows.currentIndex()))
        self.nCol = int(self.cbColumns.itemText(self.cbColumns.currentIndex()))
        # make sure it doesn't break if we give it an insufficient number of r/c's
        self.nCol = self.nCol + (self.nChan / (self.nRow + self.nCol))
    
    def _update_stream_info(self, idx):
        stream = self.cbLSLStream.itemData(idx)
        self.lbLSLFS.setText("FS: " + str(stream.nominal_srate()))
        self.lbLSLIDX.setText("Channels: " + str(stream.channel_count()))
        self.lbLSLName.setText("Name: " + str(stream.name()))
        self.lbLSLSourceID.setText("Source ID: " + str(stream.source_id()))
        self.lbLSLType.setText("Type: " + str(stream.type()))
        self.lbLSLUID.setText("UID: " + str(stream.uid()))

    def _get_current_inlet_handle(self):
        streaminfo = self.cbLSLStream.itemData(self.cbLSLStream.currentIndex())
        streaminlet = StreamInlet(streaminfo)
        print "SI ",streaminlet
        return streaminlet

    def refreshLSLStreams(self, idx):
        a=self.cbLSLStream.itemData(idx)
        print a

    def graphInGUI(self):
        self._reset_lsl_stream_select()
        self._update_stream_info(self.cbLSLStream.currentIndex())
            
    def launchGraphs(self):
        self.graphWindow = pg.GraphicsWindow()
        self.graphWindow.resize(800,800)
        self.graphWindow.setWindowTitle('Graphs')

        self.graphLineData = list()
        for c in range(self.nCol):
            for r in range(self.nRow):
                if c*self.nRow + r < self.nChan:
                    tmpplt = self.graphWindow.addPlot(title=str(c*self.nRow + r))
                    self.graphLineData.append(tmpplt.plot(pen=pg.intColor(c*self.nRow + r, hues=8)))
            self.graphWindow.nextRow()

        # get the inlet handle, _graph_upd does not do this!
        self.inlet = self._get_current_inlet_handle()
        self.graphBuf = np.zeros((len(self.chanIDX), self.graphBufSize))

        # Start an update timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._graph_upd)
        self.timer.start(0)
        
    def launchPeriodo(self):
        self.periodoWindow = pg.GraphicsWindow()
        self.periodoWindow.resize(800,800)
        self.periodoWindow.setWindowTitle('Periodograms')
        
        # Generate all line plots
        self.periodoLineData = list()
        for c in range(self.nCol):
            for r in range(self.nRow):
                if c*self.nRow + r < self.nChan:
                    tmpplt = self.periodoWindow.addPlot(title=str(c*self.nRow + r))
                    self.periodoLineData.append(tmpplt.plot(pen=pg.intColor(c*self.nRow + r, hues=8)))
            self.periodoWindow.nextRow()        
        
        # Get input length and create the buffer
        self.inlet = self._get_current_inlet_handle()
        self.periodoLen = self.inlet.channel_count / self.nChan
        self.periodoBuf = np.zeros([len(self.chanIDX), self.periodoLen])

        # Start an update timer
        self.periodoTimer = QtCore.QTimer()
        self.periodoTimer.timeout.connect(self._periodo_upd)
        self.periodoTimer.start(0)

        pass


app = QtGui.QApplication(sys.argv)
from PyQt4.QtCore import pyqtRemoveInputHook
pyqtRemoveInputHook()
form = GUITest()
form.show()
app.exec_()
