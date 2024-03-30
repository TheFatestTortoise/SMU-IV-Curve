# -*- coding: utf-8 -*-
"""
Created on Tue Mar 19 13:37:59 2024

@author: Mason

Must install pyvisa-py and pymeasure
"""
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from pymeasure.instruments.keithley import Keithley2450
from pymeasure.instruments.keithley import Keithley2400

import csv
import numpy as np

#Setup fonts
LARGE_FONT = ("Verdana", 12)
R_FONT = ("Verdana", 10)

#Parameter bounds set by documentation
minVgBound = 0
maxVgBound = 100

minVdBound = 0
maxVdBound = 100

#Initialize Tkinter GUI class
class SMU_GUI(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self)
        container.grid(row = 0, column = 0, pady = 2)
       
        frame = StartPage(container, self)
        runFrame = RunInformation(container, self)
       
        frame.grid(row = 0, column = 0, sticky = "nsew")
        runFrame.grid(row = 0, column = 0, sticky = "nsew")
       
        self.frames = {}
        self.frames[StartPage] = frame
        self.frames[RunInformation] = runFrame
        self.show_frame(StartPage)
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

#Create landing page / Main page
class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        self.controller = controller
        tk.Frame.__init__(self, parent)
       
        self.GRAPH_POINT_SIZE = 1
        self.connectedDevices = []
        self.testType = "Diode"
        self.connected = False
        
        self.device1 = None
        self.device2 = None
        
        self.device1Options = ["Select Device 1"]
        self.device2Options = ["Select Device 2", "DC Power Supply"]
       
        #Menu Setup
        self.menu = tk.Menu(self)
        self.controller.config(menu=self.menu)
       
        self.device_menu = tk.Menu(self.menu)
        self.connectK2450_menu = tk.Menu(self.menu)
        self.connectK2400_menu = tk.Menu(self.menu)
       
        self.test_menu = tk.Menu(self.menu)
       
        self.menu.add_cascade(label="Connect to...", menu = self.device_menu)
        self.menu.add_cascade(label="Change Test", menu = self.test_menu)
        
        self.device_menu.add_cascade(label = "Keithely 2450", menu = self.connectK2450_menu)
        self.device_menu.add_cascade(label = "Keithely 2400", menu = self.connectK2400_menu)

        #K2450 Sub Menu Commands
        self.connectK2450_menu.add_command(label = "USB", command = lambda: self.connectUSB("K2450"))
        self.connectK2450_menu.add_command(label = "LAN / IP", command = lambda: self.connectIPWindow("K2450"))
        self.connectK2450_menu.add_command(label = "GPIB", command = lambda: self.connectGPIB("K2450"))      

        #K2400 Sub Menu Commands
        self.connectK2400_menu.add_command(label = "USB", command = lambda: self.connectUSB("K2400"))
        self.connectK2400_menu.add_command(label = "GPIB", command = lambda: self.connectGPIB("K2400"))

        self.test_menu.add_command(label = "Diode", command = self.switchToDiode)
        self.test_menu.add_command(label = "Transistor", command = self.switchToTransistor)
       
        #Titles and Trial Name Entry
        self.TestDiodeLabel = tk.Label(self, text = "Diode Testing", font = LARGE_FONT)
        self.TestTransistorLabel = tk.Label(self, text = "Transistor Testing", font = LARGE_FONT)
        self.TestNameLabel = tk.Label(self, text = "Test Name", font = R_FONT)
        self.TestName = tk.Entry(self)
        self.GraphTitle = tk.Label(self, text = "Input Curve Preview", font = LARGE_FONT)\
        
        self.device1 = tk.StringVar(self)    
        self.device2 = tk.StringVar(self)
        
        self.device1.set("Select Device 1")
        self.device2.set("Select Device 2")
        
        self.selectDevice1 = tk.OptionMenu(self, self.device1, *self.device1Options)
        self.selectDevice2 = tk.OptionMenu(self, self.device2, *self.device2Options)

        #Gate Voltage Labels
        self.VgLabel = tk.Label(self, text = "Vg", font = R_FONT)
        self.VgMinLabel = tk.Label(self, text = "min", font = R_FONT)
        self.VgMaxLabel = tk.Label(self, text = "V | max", font = R_FONT)
        self.VgStepLabel = tk.Label(self, text = "V | Resolution", font = R_FONT)
        self.VgStepUnitsLabel = tk.Label(self, text = "Steps / Volt", font = R_FONT)

        #Drain Voltage Labels
        self.VdLabel = tk.Label(self, text = "Vd", font = R_FONT)
        self.VdMinLabel = tk.Label(self, text = "min", font = R_FONT)
        self.VdMaxLabel = tk.Label(self, text = "V | max", font = R_FONT)
        self.VdStepLabel = tk.Label(self, text = "V | Resolution", font = R_FONT)
        self.VdStepUnitsLabel = tk.Label(self, text = "# Steps", font = R_FONT)
       
        self.VgMinSV = tk.StringVar()
        self.VgMinSV.trace_add("write", self.updateGraph)
        self.VgMaxSV = tk.StringVar()
        self.VgMaxSV.trace_add("write", self.updateGraph)
        self.VgStepSV = tk.StringVar()
        self.VgStepSV.trace_add("write", self.updateGraph)
       
        self.VdMinSV = tk.StringVar()
        self.VdMinSV.trace_add("write", self.updateGraph)
        self.VdMaxSV = tk.StringVar()
        self.VdMaxSV.trace_add("write", self.updateGraph)
        self.VdStepSV = tk.StringVar()
        self.VdStepSV.trace_add("write", self.updateGraph)
       
        #Gate Voltage settings
        self.VgMin = tk.Entry(self, textvariable=self.VgMinSV)
        self.VgMax = tk.Entry(self, textvariable=self.VgMaxSV)
        self.VgStep = tk.Entry(self, textvariable=self.VgStepSV)

        #Draing Voltage Settings
        self.VdMin = tk.Entry(self, textvariable=self.VdMinSV)
        self.VdMax = tk.Entry(self, textvariable=self.VdMaxSV)
        self.VdStep = tk.Entry(self, textvariable=self.VdStepSV)
       
        #Run Buttons
        self.RunDiodeBtn = tk.Button(self, command = lambda: self.runTest("diode"), text = "Run Testing")
        self.RunTransistorBtn = tk.Button(self, command = lambda: self.runTest("transistor"), text = "Run Testing")

        #Formatting
        self.TestDiodeLabel.grid(row = 0, column = 1, sticky = 'nsew', columnspan = 7)
        self.TestNameLabel.grid(row = 1, column = 3, sticky = 'nsew')
        self.GraphTitle.grid(column = 8, row = 0)
        self.TestName.grid(row = 1, column = 4)
        
        self.selectDevice1.grid(row = 1, column = 6)
        
        '''
        self.VgMin.grid(row = 2, column = 2)
        self.VgMax.grid(row = 2, column = 4)
        self.VgStep.grid(row = 2, column = 6)
        self.VgLabel.grid(row = 2)
        self.VgMinLabel.grid(row = 2, column = 1, sticky = "nse")
        self.VgMaxLabel.grid(row = 2, column = 3, sticky = "nsew")
        self.VgStepLabel.grid(row = 2, column = 5, sticky = "nsew")
        self.VgStepUnitsLabel.grid(row = 2, column = 7, sticky = "nsew")
        '''
        
        self.VdMin.grid(row = 3, column = 2)
        self.VdMax.grid(row = 3, column = 4)
        self.VdStep.grid(row = 3, column = 6)
        self.VdLabel.grid(row = 3, column = 0, sticky = "nsew")
        self.VdMinLabel.grid(row = 3, column = 1, sticky = "nse")
        self.VdMaxLabel.grid(row = 3, column = 3, sticky = "nsew")
        self.VdStepLabel.grid(row = 3, column = 5, sticky = "nsew")
        self.VdStepUnitsLabel.grid(row = 3, column = 7, sticky = "nsew")
        self.RunDiodeBtn.grid(row = 4, column = 5)
       
        #Graphing of Input Curve
        self.fig = Figure(figsize = (4, 3), dpi = 100, facecolor = "#F0F0F0", constrained_layout = True)
        self.ax = self.fig.add_subplot(111)
        self.box = self.ax.get_position()
        self.ax.set_xlabel("V", loc = 'right', fontsize = 8)
        self.ax.get_yaxis().set_visible(False)
        self.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master = self)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row = 1, column = 8, rowspan = 3, padx = 30, pady = 20)
        
    def switchToTransistor(self):
        self.TestTransistorLabel.grid(row = 0, column = 1, sticky = 'nsew', columnspan = 7)
        self.VgMin.grid(row = 2, column = 2)
        self.VgMax.grid(row = 2, column = 4)
        self.VgStep.grid(row = 2, column = 6)
        self.VgLabel.grid(row = 2)
        self.VgMinLabel.grid(row = 2, column = 1, sticky = "nse")
        self.VgMaxLabel.grid(row = 2, column = 3, sticky = "nsew")
        self.VgStepLabel.grid(row = 2, column = 5, sticky = "nsew")
        self.VgStepUnitsLabel.grid(row = 2, column = 7, sticky = "nsew")
        self.RunTransistorBtn.grid(row = 4, column = 5)
        
        
        
        if(self.testType == "Diode"):
            self.TestDiodeLabel.grid_remove()
            self.RunDiodeBtn.grid_remove() 
            
        self.selectDevice1.grid(row = 1, column = 6)
        self.selectDevice2.grid(row = 1, column = 7)
        self.testType = "Transistor"
        
    def switchToDiode(self):
        self.TestDiodeLabel.grid(row = 0, column = 1, sticky = 'nsew', columnspan = 7)
        self.RunDiodeBtn.grid(row = 4, column = 5)
        if(self.testType == "Transistor"):
            self.VgMin.grid_remove()
            self.VgMax.grid_remove()
            self.VgStep.grid_remove()
            self.VgLabel.grid_remove()
            self.VgMinLabel.grid_remove()
            self.VgMaxLabel.grid_remove()
            self.VgStepLabel.grid_remove()
            self.VgStepUnitsLabel.grid_remove()
            self.RunTransistorBtn.grid_remove()
            self.TestTransistorLabel.grid_remove()
            
            self.selectDevice2.grid_remove()
        self.testType = "Diode"
       
    def updateGraph(self, var, index, mode):
        self.ax.cla()
        if(self.testType == "Diode"):
            self.ax.set_xlabel("V", loc = 'right', fontsize = 8)
            if (self.VdMin.get() and self.VdMax.get() and self.VdStep.get()):
                self.VdPoints = np.linspace(float(self.VdMin.get()), float(self.VdMax.get()), int(self.VdStep.get()))
                self.VgPoints = [0]
                #Vg is Y Vd is X            
                #Generate point matrix
                for point in self.VgPoints:
                    self.yArray = np.ones((1, int(self.VdStep.get()))) * point
                    self.ax.scatter(self.VdPoints, self.yArray, label = str(point), s = self.GRAPH_POINT_SIZE)
                    
                self.canvas.draw()
                
        elif(self.testType == "Transistor"):
            self.ax.set_xlabel("Vd", loc = 'right', fontsize = 8)
            self.ax.set_ylabel("Vg", loc = 'top', fontsize = 8)
       
            if (self.VdMin.get() and self.VdMax.get() and self.VdStep.get() and self.VgMin.get() and self.VgMax.get() and self.VgStep.get()):
                self.VdPoints = np.linspace(float(self.VdMin.get()), float(self.VdMax.get()), int(self.VdStep.get()))
                self.VgPoints = np.linspace(float(self.VgMin.get()), float(self.VgMax.get()), int(self.VgStep.get()))
               
                #Vg is Y Vd is X            
                #Generate point matrix
                for point in self.VgPoints:
                    self.yArray = np.ones((1, int(self.VdStep.get()))) * point
                    self.ax.scatter(self.VdPoints, self.yArray, label = str(point), s = self.GRAPH_POINT_SIZE)
                self.canvas.draw()
               
    def runTest(self, testType):
        
        try:
            
            if self.connected:
                self.controller.event_generate("<<ShowFrame - " +  testType + ">>")
                self.controller.show_frame(RunInformation)
                y = 1
        except:
            self.errorBox("No device connected")
            
    def errorBox(self, errorMsg):
        window = tk.Toplevel()
        self.window = window
        label = tk.Label(window, text = errorMsg)
        button_close = tk.Button(window, text="Cancel", command=self.window.destroy)        
        label.grid(row = 0, column = 0)
        button_close.grid(row = 1, column = 0, sticky = "nsew")
       
    def connectIPWindow(self, deviceName):
        window = tk.Toplevel()
        self.window = window
        title = tk.Label(self.window, text = deviceName)
        instructions = tk.Label(self.window, text = "Enter local device IPV4")
        self.IPEntry = tk.Entry(self.window)
        button_close = tk.Button(self.window, text="Cancel", command=self.window.destroy)    
        button_accept = tk.Button(self.window, text="Connect", command = lambda: self.connectIP(deviceName))
        title.grid(row = 0, column = 0, columnspan=2)
        instructions.grid(row = 1, column = 0, columnspan = 2)
        self.IPEntry.grid(row = 2, column = 0, columnspan = 2)
        button_accept.grid(row = 3, column = 1, sticky = "nsew")
        button_close.grid(row = 3, column = 0, sticky = "nsew")
       
    def connectIP(self, deviceName):
        IPV4 = "TCPIP::" + self.IPEntry.get() + "::INSTR"
        try:
            if(deviceName == "K2450"):
                self.connectedDevices.append(Keithley2450(IPV4))
		self.device1Options.append("Keithley2450")
                self.selectDevice1["menu"].add_command(label = self.device1Options[-1], command=lambda value=self.device1Options[-1]: self.device1.set(value))
                self.connectedDevice()
               
            elif(deviceName == "K2400"):
                self.connectedDevices.append(Keithley2400(IPV4))
                self.device1Options.append("Keithley2400")
                self.selectDevice1["menu"].add_command(label = self.device1Options[-1], command=lambda value=self.device1Options[-1]: self.device1.set(value))
                self.connectedDevice()

        except Exception as e:
            self.ipConnected = False
            self.errorBox(e)

    def connectUSB(self, deviceName):
        print(deviceName)
        self.connectedDevices.append(None)
        #self.connectedDevice()
        self.connected = True
        #USB0::0x05e6::0x2450::[serial number]::INSTR
        return(None)
    
    def connectGPIB(self, deviceName):
        GPIB = "GPIB::1"
        try:
            if(deviceName == "K2450"):
                self.connectedDevices.append(Keithley2450(GPIB))
		self.device1Options.append("Keithley2450")
                self.selectDevice1["menu"].add_command(label = self.device1Options[-1], command=lambda value=self.device1Options[-1]: self.device1.set(value))
                self.connectedDevice()
               
            elif(deviceName == "K2400"):
                self.connectedDevices.append(Keithley2400(GPIB))
		self.device1Options.append("Keithley2400")
                self.selectDevice1["menu"].add_command(label = self.device1Options[-1], command=lambda value=self.device1Options[-1]: self.device1.set(value))
                self.connectedDevice()
                
        except Exception as e:
            self.ipConnected = False
            self.errorBox(e)
    def connectedDevice(self):
        self.menu.entryconfigure(1, label = "✔" + str(len(self.connectedDevices)) + "Connected")
        #Initialize SMU parameters
        try:
            self.connectedDevices[-1].reset()
            self.connectedDevices[-1].use_front_terminals()
            self.connected = True

        except Exception as e:
            self.ipConnected = False
            self.errorBox(e)
class RunInformation(tk.Frame):
    def __init__(self, parent, controller):
        self.controller = controller
        tk.Frame.__init__(self, parent)
        #Bind to runSMU when the frame is shown so it doesn't look for nonexistent information
        self.bind("<<ShowFrame>>", self.runSMU)
       
        #Control Buttons
        self.SaveALLBtn = tk.Button(self, text = "Quit and Save All")
        self.SaveRAWBtn = tk.Button(self, command = self.saveRaw, text = "Quit and Save Raw Data")
        self.QuitBtn = tk.Button(self, command = self.quitConformation, text = "Quit Without Saving")

        #Graphing of Input Curve
        self.fig = Figure(figsize = (5, 3.5), dpi = 100, facecolor = "#F0F0F0", constrained_layout = True)
        self.t = np.arange(0, 100, .01)
        self.ax = self.fig.add_subplot(111)
        self.line, = self.ax.plot(self.t, 2 * np.sin(2 * self.t))
        self.ax.set_xlabel("Vds", loc = 'right', fontsize = 8)
        self.ax.set_ylabel("Id", loc = 'top', fontsize = 8)
        self.canvas = FigureCanvasTkAgg(self.fig, master = self)
        self.canvas.draw()
       
        #Formatting
        self.SaveALLBtn.place(x = 220, y = 50)
        self.SaveRAWBtn.place(x = 200, y = 150)
        self.QuitBtn.place(x = 210, y = 250)
        self.canvas.get_tk_widget().place(x = 500, y = 20)
        self.IV_curve_data = []
        
        '''
        for Vg in self.controller.VgPoints:
            self.smu.source_voltage = Vg
            Vd_Id_data = []
           
            for Vd in self.controller.VdPoints:
                self.smu.source_voltage = Vd
                Id = self.smu.current
                Vd_Id_data.append((Vd, Id))
            self.IV_curve_data.append((Vg, Vd_Id_data))

        self.smu.shutdown()
        '''
        
    def runSMU(self):
        try:
            self.smu = self.controller.smu
            self.trigger = self.smu.trigger()
           
            self.smu.defbuffer1.clear()
            self.smu.measure.func = self.smu.FUNC_DC_CURRENT
            self.smu.source.fun = self.smu.FUNC_DC_VOLTAGE
           
            self.smu.measure.sense = self.smu.SENSE_4WIRE
            self.smu.measure.autorange = self.smu.ON
            self.smu.measure.np1c = 1
           
            self.smu.source.highc = self.smu.OFF
            self.smu.source.range = 2
            self.smu.source.ilimit.level = 1
            self.smu.source.sweeplinear("diode", self.controller.VgMin.get(), self.controller.VgMax.get(), self.controller.VgSteps.get(), 0.1)
           
            self.trigger.initiate()
            self.trigger.waitcomplete()
           
            self.data = []
            if self.smu.defbuffer1.n == 0:
                self.errorBox("Buffer is empty")
            else:
                for i in range(1, self.defbuffer1.n + 1):
                    self.data.append([
                        self.defbuffer1.sourcevalues[i],
                        self.defbuffer1.readings[i],
                        self.defbuffer1.relativetimestamps[i]])
            self.smu.shutdown()
        except Exception as e:
            self.errorBox(e)

    def saveCSV(self, saveLocation):
        csv_filename = saveLocation + self.TestName + "measurement_data.csv"

        with open(csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Voltage (V)", "Current (A)"])
            writer.writerows(self.data)
    def saveAll(self):
        saveLocation = self.selectSaveLocation()
       
        #Graph Saving
        graphFileName = saveLocation + self.TestName + "graph.png"
        self.fig.savefig(graphFileName)
        self.saveCSV(self.saveLocation)
        self.quitConformation("All data has been saved, are you sure you want to quit?")
       
    def saveRaw(self):
        saveLocation = self.selectSaveLocation()
        self.saveCSV(saveLocation)
        self.quitConformation("Are you sure you want to quit without saving the graph?")
       
    def selectSaveLocation(self):
        saveLocation = tk.filedialog.askdirectory(initialdir = '/', title = 'Select Save Directory')
        return saveLocation
    def quitConformation(self, quitText = ""):
        window = tk.Toplevel()
        self.window = window
        if (quitText == ""):
            label = tk.Label(window, text = "Are you sure you want to quit without saving?")
        else:
            label = tk.Label(window, text = quitText)
           
        button_cancel = tk.Button(window, text="Cancel", command=self.window.destroy)
        button_close = tk.Button(window, text="Ok", command=self.twoWindowsOneCommand)
       
        label.grid(row = 0, column = 0, columnspan= 2)
        button_close.grid(row = 1, column = 0, sticky = "nse")
        button_cancel.grid(row = 1, column = 1, sticky = "nsw")
       
    def twoWindowsOneCommand(self, page = StartPage):
        self.window.destroy()
        self.controller.show_frame(page)
        
    def errorBox(self, errorMsg):
        window = tk.Toplevel()
        self.window = window
        label = tk.Label(window, text = errorMsg)
        button_close = tk.Button(window, text="Cancel", command=self.window.destroy)        
        label.grid(row = 0, column = 0)
        button_close.grid(row = 1, column = 0, sticky = "nsew")
        
app = SMU_GUI()
app.mainloop()
