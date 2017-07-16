# -*- coding: utf-8 -*-
"""
Created on Fri Jul 14 23:47:59 2017

@author: marzipan
"""

from PySide.QtCore import *
from PySide.QtGui import * 
import sys
import time

class AlphaScanGui(QWidget):
    def __init__(self, Device, fileName, parent=None):
        super(AlphaScanGui, self).__init__(parent)
        self._Device = Device
        
        # Creat main layout
        mainLayout =  QVBoxLayout()
        self.setLayout(mainLayout)
        
        # Create tab widget
        tabWidget =  QTabWidget()
        mainLayout.addWidget(tabWidget)
        
        # Create persistent status area
        statusArea = QVBoxLayout()
        mainLayout.addLayout(statusArea)
        
        # Add device streaming and connected labels to status area
        self.StreamingStatus = QLabel("Not Streaming") 
        self.ConnectionStatus = QLabel("Not Connected")
        self.DebugConsole = QTextEdit("Debug Console...")
        self.DebugConsole.setReadOnly(True)
        
        statusArea.addWidget(self.StreamingStatus)
        statusArea.addWidget(self.ConnectionStatus)
        statusArea.addWidget(self.DebugConsole)

        # Create tab objects        
        self.genTab = GeneralTab(self._Device, self.DebugConsole)  
        self.apTab = AP_TAB(self.DebugConsole)
        self.fsTab = FS_TAB(self._Device, self.DebugConsole)
        self.sysTab = SYS_TAB(self._Device, self.DebugConsole)
        self.adcTab = ADC_REG_TAB(self._Device, self.DebugConsole)
        self.pwrTab = PWR_REG_TAB(self._Device, self.DebugConsole)
        self.acclTab = ACCEL_REG_TAB(self._Device, self.DebugConsole)
        self.vizTab = VIZ_TAB(self._Device, self.DebugConsole)
        self.statsTab = STATS_TAB(self._Device, self.DebugConsole)
        self.storTab = STOR_TAB(self._Device, self.DebugConsole)
        self.checkTab = SYSCHECK_TAB(self._Device, self.DebugConsole)
        
        # Create tabs with objects
        tabWidget.addTab(self.genTab, "General")
        tabWidget.addTab(self.apTab,"AcessPoint")
        tabWidget.addTab(self.fsTab, "FileSystem")
        tabWidget.addTab(self.sysTab, "McuParams")
        tabWidget.addTab(self.adcTab, "ADC")
        tabWidget.addTab(self.pwrTab, "Power")
        tabWidget.addTab(self.acclTab, "Accel") 
        tabWidget.addTab(self.vizTab, "Graph")
        tabWidget.addTab(self.statsTab, "Stats")
        tabWidget.addTab(self.storTab, "Storage")
        tabWidget.addTab(self.checkTab, "SysCheck")

        # Connect tab change event to handler        
        tabWidget.currentChanged.connect(self.onTabChange) #changed!

        self.setWindowTitle("AlphaScan Controller")
        
        # Connect signals
        self.sysTab.SIG_reserve_tcp_buffer.connect(self.genTab.disable_auto_connect)
        self.fsTab.SIG_reserve_tcp_buffer.connect(self.genTab.disable_auto_connect)
        
        # Create periodic timer for updating streaming and connection status
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(100) # interval in milliseconds...
        
        # Lock app width
        self.setFixedWidth(self.geometry().width())
    
    @Slot()
    def update(self):
        if self.genTab.Streaming:
            self.StreamingStatus.setText("Streaming")
        else:
            self.StreamingStatus.setText("Not Streaming")
        if self.genTab.Connected:
            self.ConnectionStatus.setText("Connected")
        else:
            self.ConnectionStatus.setText("Not Connected")
        
    @Slot() 
    def onTabChange(self,i): #changed!
        #TODO send signal to VIZ_Tab to start/stop plotting
        if (i == 7): #TODO make this not hard coded!
            #self.vizTab.start_plotting()
            pass
        else:
            #self.vizTab.stop_plotting()
            pass
                  
    def closeEvent(self, event):
        self._Device.close_event()
        event.accept()
        