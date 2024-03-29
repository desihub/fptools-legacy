import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import matplotlib.pyplot as plt
import sys,os
sys.path.append('/home/msdos/focalplane/plate_control/trunk/petal')
import petalcomm
import petal
import pandas as pd
import datetime
import time, datetime
import pickle
import csv
from scipy import interpolate
import json
import argparse
from matplotlib.figure import Figure
import tkinter as tk
import numpy as np

import petalcomm
import petal

import tkinter.filedialog
import tkinter.messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import pandas as pd

# nominal hole location data

class PosPlottingApp(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg = 'white')
        self.start_time = datetime.datetime.now()
        self.file_path = '/home/msdos/focalplane/pos_utility/'
        self.temp_log_path = os.getcwd()#'/home/msdos/test_util/temp_logs/'
        self.pos_index_file = 'desi_positioner_indexes.csv'
        

        self.hole_coords = np.genfromtxt(self.file_path+'hole_coords.csv', delimiter = ',', usecols = (3,4), skip_header = 40)
        self.nons = [38, 331, 438, 460, 478, 479, 480, 481, 497, 498, 499, 500, 513, 514, 515, 516, 527, 528, 529, 530, 531, 535, 536, 537, 538, 539, 540]
        self.gifs = [541, 542]
        self.fifs = [11, 75, 150, 239, 321, 439, 482, 496, 517, 534]

        self.collect_data = False
        self.wait = 120
        self.num_times = 0
        self.power_off = False

        self.mt = []
        self.mean_temp = []
        self.can_buses= {'can10','can11','can12','can13','can14','can15','can16','can17','can22','can23'}
        self.pb_temps = {'PBOX_TEMP_SENSOR':[], 'FPP_TEMP_SENSOR_1': [], 'FPP_TEMP_SENSOR_2': [], 'FPP_TEMP_SENSOR_3': [], 'GXB_TEMP_SENSOR': []}
        self.adc_values = {'ADC2': [], 'ADC3': [], 'ADC1': [], 'ADC4': [], 'ADC0': []}

        self.createWidgets()


    def createWidgets(self):
        window = tk.Frame(bg = 'white')
        window.pack(side='top', fill='both')
        self.plot_window = tk.Frame(bg = 'white')
        self.plot_window.pack(side='bottom', fill='both')

        #set PC
        self.PC_entry = tk.Entry(window, width = 8, justify = 'right')
        self.PC_entry.grid(column=0, row=0)
        self.PC_button = tk.Button(window, width = 10, text = 'CONNECT TO PC', command=lambda: self.set_PC())
        self.PC_button.grid(column=0,row=1)

        #wait time
        self.wait_time_entry = tk.Entry(window, width = 8, justify = 'right')
        self.wait_time_entry.grid(column=2, row=0)
        self.wait_time_entry.insert(0, self.wait)
        self.wait_time_button = tk.Button(window, width = 10, text = 'WAIT TIME', command=lambda: self.set_wait())
        self.wait_time_button.grid(column=2,row=1)
        print("Waiting %s seconds between calls" % str(self.wait))

        #Start & Stop
        self.start_button = tk.Button(window, width = 10, text = 'START', command=lambda: self.start())
        self.start_button.grid(column=3, row=0)
        #self.stop_button = tk.Button(window, width = 10, text = 'STOP', command=lambda: self.stop())
        #self.stop_button.grid(column=3, row=1)

        #Quit Button
        #self.quit_button = tk.Button(window, width = 10, text = 'QUIT', command=lambda: self.quit())
        #self.quit_button.grid(column=4, row=0)


    def set_PC(self):
        Petal_to_PC = {0:4, 1:5, 2:6, 3:3, 4:8, 5:10, 6:11, 7:2, 8:7, 9:9, 18:0}
        self.PC = int(self.PC_entry.get())
        self.petal = Petal_to_PC[self.PC]
        self.comm = petalcomm.PetalComm(self.PC)
        petal_label = print("Connected to PC%s on Petal %s" % (str(self.PC), str(self.petal)))

        df = pd.read_csv(self.pos_index_file)
        self.pdf=df.loc[df['PETAL_ID'] == int(self.petal)]

    def set_wait(self):
        self.wait = int(self.wait_time_entry.get())
        print("Waiting %s seconds between calls" % str(self.wait))

    def start(self):
        self.collect_data = True
        print("Data is being collected")
        self.run()


    def stop(self):
        self.collect_data = False
        print("Data not being collected")

    def quit(self):
        sys.exit()

    def get_temps(self):
        self.current_time = datetime.datetime.now()
        print("Taking Temp Data: ", self.current_time)
        self.mt.append(self.current_time)
        
        current_pos_dict = self.comm.pbget('posfid_temps')
        #Check if power is on
        total = 0 
        for can in self.can_buses:
            num = len(current_pos_dict[can])
            total += num
        if total == 0:
            print("Power not on")
            self.power_off = True

        pb_dict = self.comm.pbget('pb_temps')
        adc_dict = self.comm.pbget('adcs')
        if self.power_off == True:
            self.mean_temp.append(np.nan)
        else:
            self.all_temps = []
            self.ids = []
            for can, val in current_pos_dict.items():
                for i, t in val.items():
                    self.all_temps.append(t)
                    self.ids.append(i)
            self.mean_temp.append(np.mean(self.all_temps))

        for i in self.pb_temps.keys():
            try:
                self.pb_temps[i].append(pb_dict[i])
            except:
                self.pb_temps[i].append(np.nan)

        for i in self.adc_values.keys():
            try:
                self.adc_values[i].append(adc_dict[i])
            except:
                self.adc_values[i].append(np.nan)

        D = {self.current_time: [current_pos_dict, pb_dict, adc_dict]}
        print(D)
        #Start Temperature log
        self.temp_log = open(self.temp_log_path+'/temp_log_PC_%s.txt'%str(self.PC),'a+')

        self.temp_log.write(str(D))
        self.temp_log.write('\n')
        self.temp_log.close()
        print('wrote temp log')

        self.make_plot()


    def make_plot(self):
        if self.num_times > 0:
            try:
                self.canvas.get_tk_widget().destroy()
            except:
                pass
        fig = Figure(figsize=(12,6))
        gs = fig.add_gridspec(3, 3)
        ax1 = fig.add_subplot(gs[0:2, :])
        ax2 = fig.add_subplot(gs[2, 0])
        ax3 = fig.add_subplot(gs[2, 1])
        ax4 = fig.add_subplot(gs[2, 2])

        ax1.set_title(self.current_time)
        if self.power_off == False:  
            bins = np.linspace(np.min(self.all_temps), np.max(self.all_temps), 25)
            pos_temps = np.array(self.all_temps)[np.where(np.array(self.ids) < 10000)[0]]
            fid_temps = np.array(self.all_temps)[np.where(np.array(self.ids) > 10000)[0]]
            ax2.hist(pos_temps, bins = bins, label = 'Pos')
            ax2.hist(fid_temps, bins=bins, label = 'Fids')
            ax2.legend(prop={'size': 6})

        mt = [m.strftime("%H:%M:%S") for m in self.mt]
        ax3.plot(mt, self.pb_temps['PBOX_TEMP_SENSOR'], '-x', label = 'PBOX')
        ax3.plot(mt, self.pb_temps['FPP_TEMP_SENSOR_1'], '-x', label = 'FPP1')
        ax3.plot(mt, self.pb_temps['FPP_TEMP_SENSOR_2'], '-x', label = 'FPP2')
        ax3.plot(mt, self.pb_temps['FPP_TEMP_SENSOR_3'], '-x', label = 'FPP3')
        ax3.plot(mt, self.pb_temps['GXB_TEMP_SENSOR'], '-x', label = 'GXB')
        ax3.plot(mt, self.mean_temp, '-x', label = 'Mean POS')
        ax3.legend(prop={'size': 6})
        ax3.set_xticklabels(mt, rotation=45)

        ax4.plot(mt, self.adc_values['ADC2'], '-x', label = 'ADC2')
        ax4.plot(mt, self.adc_values['ADC3'], '-x', label = 'ADC3')
        ax4.plot(mt, self.adc_values['ADC1'], '-x', label = 'ADC1')
        ax4.plot(mt, self.adc_values['ADC4'], '-x', label = 'ADC4')
        ax4.plot(mt, self.adc_values['ADC0'], '-x', label = 'ADC0')
        ax4.legend(prop={'size': 6})
        ax4.set_xticklabels(mt, rotation=45)

        for i in range(len(self.hole_coords)):
            x = self.hole_coords[i][0]
            y = self.hole_coords[i][1]

            if i not in self.nons:
                ax1.plot(x, y, color = 'lightgrey', marker='o', zorder = -1)
                if i in self.fifs:
                    text = 'F' + str(i)
                    col = 'blue'
                elif i in self.gifs:
                    text = 'G' + str(i)
                    col = 'purple'
                else:
                    text = i
                    col = 'black'
                ax1.text(x-.1, y + 0.3, text, color = col, fontsize=6)

        self.hole=1
        ax1.scatter(self.hole_coords[self.hole][0], self.hole_coords[self.hole][1], marker= '*', s=200, color = 'gold')

        self.dev_list=self.pdf['CAN_ID'].tolist()
        self.hole_list=self.pdf['DEVICE_LOC'].tolist()
        self.dev_id_loc=dict(zip(self.dev_list,self.hole_list))

        if self.power_off == False:
            holes = []
            idx = []
            for i,e in enumerate(self.ids):
                try:
                    holes.append(self.dev_id_loc[e])
                    idx.append(i)
                except:
                    print('failed: ',e)
                    self.nons.append(e)
                    pass
            temps = np.array(self.all_temps)[np.array(idx)]

            x = []
            y = []
            idx2 = []
            for i,e in enumerate(holes):
                try:
                    x.append(self.hole_coords[int(e)][0])
                    y.append(self.hole_coords[int(e)][1])
                    idx2.append(i)
                except:
                    print('failed: ',new_ids[i])
                    self.nons.append(new_ids[i])
                    pass
            temps = temps[np.array(idx2)]
            x = np.array(x)
            y = np.array(y)

            sc = ax1.scatter(x,y,s=120,c=temps)
            self.cbar = plt.colorbar(sc, ax=ax1)
        self.canvas = FigureCanvasTkAgg(fig, master=root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas._tkcanvas.pack()
  
        fig.canvas.draw()
        self.canvas.draw()
        
        self.num_times += 1

    def run(self):
        while self.collect_data:
            self.get_temps()
            time.sleep(self.wait)

if __name__ == '__main__':
    root=tk.Tk()
    root.title("Positioner Temp. Plotting")
    P=PosPlottingApp(master=root)
    #P.after(1000, P.run)
    P.mainloop()
    




        
