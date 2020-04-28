#!/usr/bin/python3
"""
Monitor2
Pulls out key metrics using recorded ventilator data from:
https://github.com/hahnicity/ventmode/tree/master/anon_test_data/raw_vwd
after being converted to csv_raw files. See converted data for this
model here:
https://github.com/Eric-11/ventilator-parameters/tree/master/models/cvs_raw

Copyright (C) 2020 Eric Baicy

This program is free software: you can redistribute it and/or modify it under 
the terms of the GNU General Public License as published by the Free Software 
Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT 
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with 
this program. If not, see <https://www.gnu.org/licenses/>.
"""

import numpy as np
import matplotlib.pyplot as plt
import time
from pathlib import Path
import model2

#
# Notes on Parameters
#
# PEEPi - Intrinsic positive end-expiratory pressure (PEEP) or auto-PEEP is a
# complication of mechanical ventilation that most frequently occurs in
# patients with COPD or asthma who require prolonged expiratory phase of
# respiration. These patients may have difficulty in totally exhaling the
# ventilator-delivered tidal volume before the next machine breath is
# delivered. When this problem occurs, a portion of each subsequent tidal
# volume may be retained in the patient's lungs, a phenomenon sometimes
# referred to as breath stacking (see image below). If this goes unrecognized,
# the patient's peak airway pressure may increase to a level that results in
# barotrauma, volutrauma, hypotension, patient-ventilator dyssynchrony, or
# death.
#  - https://www.medscape.com/answers/304068-104803/what-is-intrinsic-positive-end-expiratory-pressure-peep-or-auto-peep-in-mechanical-ventilation
#
# dP - Driving Pressure https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4356532/
# https://jintensivecare.biomedcentral.com/articles/10.1186/s40560-018-0334-4
# The difference between plateau pressure and positive end-expiratory pressure
# (Pplat-PEEP), and can also be expressed as the ratio of tidal volume to
# respiratory system compliance (Vt/Crs)
# ************************************************************************
# *** ARDS patients demonstrated that driving pressure is the variable ***
# *** that is most strongly associated with mortality                  ***
# ************************************************************************
#
# Pl - Transpulmonary Pressure
# https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5537111/
# Transpulmonary pressure is the difference between the alveolar pressure
# and the intrapleural pressure in the pleural cavity. During human
# ventilation, air flows because of pressure gradients.
# Ptp = Palv – Pip. Where Ptp is transpulmonary pressure, Palv is alveolar
# pressure, and Pip is intrapleural pressure.
#    *** unclear how to measure without additional input ***
#
# P01 - Occulsion pressure https://www.ncbi.nlm.nih.gov/pubmed/9382227
#       https://annalsofintensivecare.springeropen.com/articles/10.1186/s13613-019-0576-x
#
# PTPmin - pressure time product per minute
# https://www.ncbi.nlm.nih.gov/pubmed/15101863
# The pressure time product (PTP) is the product of the average inspiratory
# pressure (starting from the onset of effort) and the duration of inspiration:
# PTP = Pavg × Ti.
# The PTP was developed to account for energy expenditures during the dynamic
# and isometric phases of respiration. Therefore, the PTP will more directly
# measure the total energy (in addition to the total work) of breathing.
# https://ccforum.biomedcentral.com/articles/10.1186/cc3516
#
# NOT COMPLETED: tidal volume (Tv)  and transpulmonary pressure (Pl)
#


class MONITOR2:

    models = ''
    data = []
    datanp = np.empty(0)
    captured = []  # list of start/end points of cycles
    captured_idx = []  # indices of start/end points in data sample
    peep_min = 0
    peak = 0
    peak_idx = 0
    bps = 0
    max_time = 0
    threshold = 0  # trigger level for breath cycle
    threshold_factor = 1.25
    random = [0, 0, 0]  # percentage range for random varation in simulations

    # Stats taken from:
    # The basics of respiratory mechanics: ventilator-derived parameters
    # Pedro Leme Silva, Patricia R. M. Rocco
    stats = {
        "PEEP": 0,    # PEEP pressure
        "PEEPi": 0,   # Intrinsic PEEP presure
        "Ppeak": 0,   # Peak pressure
        "FlowI": 0,   # Inspiratory inflow time
        "Ipause": 0,  # Inspiry pause time
        "FlowE": 0,   # Expiratory flow time
        "Epause": 0,  # Expiratory pause time
        "Pplat": 0,   # Plateau Pressure
        "Start": 0,   # start time of cycle
        "End": 0,     # end time of cycle
        "Vt": 0,      # tidal volume - @TODO
        "dP": 0,      # driving pressure
        "Pl": 0,      # transpulmonary pressure - @TODO
        "P01": 0,     # Occlusion pressure
        "PTP": 0,     # pressure-time product per breath cycle
        "RR": 0       # breaths per min. based on current cycle speed
    }

    cycle_stats = []  # array of all cycle stats computed for data

    def __init__(self, model_file=''):
        print("Setting up model.")
        self.models = model2.BREATH2(filename=model_file)

    def plot(self, title=''):
        """
        Plots the sampled data
        """
        fig = plt.figure()
        ax1 = fig.add_subplot(1, 1, 1)

        xar = []
        yar = []
        for eachLine in self.data:
            if len(eachLine) > 1:
                x, y = eachLine[1], eachLine[0]
                yar.append(float(y))
                xar.append(float(x))

        if title != '':
            ax1.set_title(title)
        # waveform
        ax1.plot(yar, xar)
        plt.show()

    def plot_diff(self, title=''):
        """
        Plots waveform and the differential of data
        """
        fig = plt.figure()
        ax1 = plt.subplot(211)
        ax2 = plt.subplot(212, sharex=ax1)

        xar = []
        yar = []
        for eachLine in self.data:
            if len(eachLine) > 1:
                x, y = eachLine[1], eachLine[0]
                yar.append(float(y))
                xar.append(float(x))

        x0 = 0
        y0 = 0
        diff = []
        for x, y in self.data:
            m = (y - y0) / (x - x0)
            x0 = x
            y0 = y
            diff.append(m)
        diff = np.array(diff)
                
        if title != '':
            ax1.set_title(title)
        # waveforms
        ax1.plot(yar, xar)
        ax2.plot(yar, diff)
        plt.show()

    def compute(self, plot=True, title=''):
        """
        Computes parameters of all cycle samples in self.data

        Uses: find_cycles -> contours
        """
        self.datanp = np.array(self.data)  # convert to numpy array quickly

        peak = np.amax(self.datanp, axis=0)  # peak value
        peak_idx = np.argmax(self.datanp, axis=0)  # index with peak value
        peep_min = np.amin(self.datanp, axis=0)  # peep value

        # convert to scalar from 2d array of [time, pressure]
        self.peak_idx = peak_idx[1]
        self.peep_min = peep_min[1]  # floor of pressure readings (PEEP)
        self.peak = peak[1]
        self.max_time = peak[0]

        if self.threshold == 0:
            threshold = self.peep_min * self.threshold_factor  # factor for trigger
        else:
            threshold = self.threshold

        if plot:
            self.fig = plt.figure()
            self.ax1 = self.fig.add_subplot(211)
            self.ax2 = self.fig.add_subplot(212, sharex=self.ax1)

            if title != '':
                self.ax1.set_title(title)

        self.threshold = threshold
        self.find_cycles(threshold)  # find start/end points of each cycle

        for i in range(0, int(len(self.captured) / 2)):
            self.contours(i, threshold, plot)  # find points in cycle i
            self.cycle_stats.append(self.stats)  # build list of dictionary stats
                    
        if plot:
            # rescale and display
            self.ax1.set_ylim(bottom=-5, top=self.peak*1.3)
            self.ax2.autoscale(axis='y')
            plt.show()

    def find_cycles(self, threshold, plot=True):
        """
        Sweeps through captured data and finds breath cycles

        Updates "captured" array with start [time, pressure] and end
        [time, pressure] of full respitory cycles detected in the data.
        The detection is simple threshold crossings based on the minimum
        value found in the data sample.
        """
        # xar is shifted to threshold
        xar = np.subtract(self.datanp[:, 1], threshold)
        breath_cnt = (np.diff(np.sign(xar)) != 0).sum()  # count crossings

        # floor divide - > 3 crossings indicate 1 full breath cycle captured
        # not used, just for illustration
        breath_cnt = breath_cnt // 3

        # algorithm to seperate each full cycle from data
        state = 0
        captured = []
        captured_idx = []
        for i in range(1, len(xar)):
            # Looking for patterns in Negative (N) and Positive (P) crossings
            # searching for sequence of N->P, P->N, N->P = full cycle
            if state == 0 and xar[i] < 0:
                # find first negative region N
                state = 1
            elif state == 1 and xar[i] > 0:
                # positive region N->P Found
                captured.append(self.data[i])  # start of inhalation
                captured_idx.append(i)  # index of event
                state = 2
            elif state == 2 and xar[i] < 0:
                state = 3  # start of pause P->N Found
            elif state == 3 and xar[i] > 0:                # end of pause and start of next inhalation N->P
                captured.append(self.data[i])
                captured_idx.append(i)  # index of event
                state = 1

        if (len(captured) % 2) != 0:
            # incomplete cycle found
            captured.pop()  # partial waveform found remove start point
            captured_idx.pop()
        self.captured = captured  # start/end pairs
        self.captured_idx = captured_idx  # start/end indices

    def contours(self, cycle=0, threshold=10, plot=True):
        """
        Computes assents, descents and plateaus in selected cycle of waveform
        and it extracts some key parameters for stats dictionary

        Note the point of detecting where slope flattens is based on finding
        where the value is 1/factor of peak slope, where factor = the divisor
        """
        
        factor = 10  # divisor of peak slope to determine when it is flattening

        if len(self.captured) % 2 > cycle:
            # requested cycle doesn't exist in waveform
            return
        # Get interval of cycle to analyze
        cycle = cycle * 2  # cycles are in pairs start, end
        start = self.captured_idx[cycle]
        end = self.captured_idx[cycle + 1]

        # section off data for analysis, may need to widen start/stop points
        # for a bigger window
        self.datanp = np.array(self.data)  # copy over cycle to analyze
        data_cycle = self.datanp[start:end, :]  # slice cycle

        peak = np.amax(data_cycle, axis=0)[1]
        peak_idx = np.argmax(data_cycle, axis=0)[1]
        peep_min = np.amin(data_cycle, axis=0)[1]

        if plot:
            if cycle == 0: # only plot if starting on cycle 0
                self.xar = []
                self.yar = []
                for eachLine in self.data:
                    if len(eachLine) > 1:
                        x, y = eachLine[1], eachLine[0]
                        self.yar.append(float(y))
                        self.xar.append(float(x))

                self.ax1.plot(self.yar, self.xar)
                self.ax1.plot([self.yar[0], self.yar[-1]], [threshold, threshold], 'r:')
                self.ax1.text(self.yar[int(len(self.yar) / 2)], threshold, "Threshold {:1.1f}".format(threshold))
                for i in range(0, len(self.captured), 2):
                    self.ax1.text(self.captured[i][0], 0, "S")  # Start cycle
                    self.ax1.text(self.captured[i + 1][0],
                             0,"E", horizontalalignment='right')  # End cycle

        # Inhalation and Exhalation Detection Method
        #
        # Take the derivative of the waveform
        # find min and max which will give a rough estimate of when
        # in time the inhalation and expiration occur
        # bracket the two min and maxs by looking for when the slope
        # approaches a scaled value of the maximum

        # Use the differential to detect slope
        # this is a descrete calculation of just (x1-x0)/(y1-y0),
        # (x2-x1)/(y2-y1)...(xn-xn-1)/(yn - yn-1)
        x0 = 0
        y0 = 0
        diff = []
        avg_time_samples = 0
        for x, y in data_cycle:
            m = (y - y0) / (x - x0)
            avg_time_samples += (y - y0)  # compute average time spacing for samples
            x0 = x
            y0 = y
            diff.append(m)
        diff = np.array(diff)
        avg_time_samples /= len(diff)

        ##
        # Samples to move past peak before seaching for minimum
        ##
        skip = int(round(0.3 / avg_time_samples, 0))

        # find peak positive
        diff_max = np.amax(diff)  # max value
        idx_max = np.argmax(diff)  # index for max point (start inhalation)
        # find peak minimum after maximum has occured
        if idx_max + skip > len(diff):
            print("*** Warning @{}s max occured near end of threashold cycle".format(data_cycle[idx_max][0]))
            skip = 0
        diff_min = np.amin(diff[idx_max + skip:])  # min value
        # For some reason np.argmin doesn't work properly
        # idx_min = np.argmin(diff[idx_max + skip:])
        # do manual search for minimum
        find=0
        find_idx=0
        for x in range(idx_max+skip, len(diff)):
            if diff[x] < find:
                find=diff[x]
                find_idx=x
        idx_min=find_idx
        
        # idx_max is index for peak max value
        # idx_min is now suspected center peak for exhale

        # bracket inhalation slope down to start
        idx_max_start = 0  # initial value
        for n in range(idx_max, -1, -1):
            # find start of inhalation
            # print(n, diff[n], diff_max/factor)
            if diff[n] < diff_max/factor:
                idx_max_start = n
                break
        if idx_max_start < 1:
            # this condition happens often as the trigger is usually the
            # start of the cycle
            # print("*** WARNING {}s start of inhalation probably invalid".format(data_cycle[idx_max_start][0]))
            pass

        # bracket inhalation slope up to min location
        # test from max to min location
        idx_max_end = idx_min  # initial value
        for n in range(idx_max, idx_min):
            if diff[n] < diff_max/factor:
                idx_max_end = n
                break
        if idx_max_end == idx_min:
            print("*** WARNING {}s end of inhalation not detected".format(data_cycle[idx_max_end][0]))

        # Find exhalation points
        # bracket exhalation slope down to start
        idx_min_start = idx_max  # initial value
        for n in range(idx_min, peak_idx, -1):
            # find start of exhalation
            if diff[n] >= diff_min/factor:
                idx_min_start = n
                break
        if idx_min_start == 0:
            print("*** WARNING {}s start of exhalation probably invalid".format(data_cycle[idx_min_start][0]))

        # bracket exhalation slope up to end location
        # test from max to min location
        idx_min_end = len(diff)  # initial value

        for n in range(idx_min, len(diff)):
            # find end of exhalation
            if diff[n] >= diff_min/factor:
                idx_min_end = n
                break

        if idx_min_end == len(diff):
            print("*** WARNING {}s end of exhalation not detected".format(data_cycle[len(diff)][0]))

        #    
        # print("max start {}, {}, max {}, {}, max end {}, {}\n".format(idx_max_start,data_cycle[idx_max_start][1],
        #                                                           idx_max, data_cycle[idx_max][1],
        #                                                           idx_max_end,data_cycle[idx_max_end][1]))
        # print("min start {}, {}, min {}, {}, min end {}, {}\n".format(idx_min_start,data_cycle[idx_min_start][1],
        #                                                           idx_min, data_cycle[idx_min][1],
        #                                                           idx_min_end,data_cycle[idx_min_end][1]))

        if plot:
            # show peak
            self.ax1.plot([data_cycle[peak_idx][0]], [peak], 'ro')
            self.ax1.text(data_cycle[peak_idx][0], peak * 1.02, "Peak {:2.1f}".format(peak))

            # Show differential crossings cycle
            self.ax2.set_title("Differential")
            self.ax2.plot(self.yar[start:end], diff)
            self.ax2.plot([self.yar[start],self.yar[-1]], [0,0])  # reference crossings
        
        if plot:
            self.ax1.plot([data_cycle[idx_min_start][0], data_cycle[idx_min_start][0]], [0, peak],
                     'r:')  
            self.ax1.plot([data_cycle[idx_min_end][0], data_cycle[idx_min_end][0]], [0, peak],
                     'r-') 
            
            self.ax1.plot([data_cycle[idx_max_start][0], data_cycle[idx_max_start][0]], [0, peak],
                     'g:')  # second minium found -- start
            self.ax1.plot([data_cycle[idx_max_end][0], data_cycle[idx_max_end][0]], [0, peak],
                     'g-')  # second minium found -- end

            # Plot Plateau
            self.ax1.plot(data_cycle[idx_min_start][0], data_cycle[idx_min_start][1], 'r*')
            self.ax1.text(data_cycle[idx_min_start][0], data_cycle[idx_min_start][1], "Pplat {:2.1f}".format(data_cycle[idx_min_start][1]))


        # Find P01 100ms into inhalation
        # linear interpolation to find value
        P01 = np.interp(self.data[start][0] + 0.1,
                        data_cycle[:, 0], data_cycle[:, 1])
        if plot:
            ydelta = (self.data[start+4][0] - self.data[start][0])/5
            jump = int(0.1/ydelta)  # estimate index @ 0.1s for plotting
            self.ax1.plot([self.data[start+jump][0]], [P01], 'ro')
            self.ax1.text(self.data[start+jump][0], P01, "P0.1 {:2.1f}".format(P01))

        # Find PTP for cycle
        PTPavg = np.average(data_cycle[0:peak_idx], axis=0)[1]
        if plot:
            text = "PTP={:2.1f}".format(PTPavg)
            self.ax1.text(self.data[int(start+peak_idx/2)][0], peep_min, text,
                     verticalalignment='top')

        # PEEPi
        # end may not the best spot to use because it's the start
        # of the next inhalation cycle at the threshold point
        # Also high PEEPi values might interfere with threshold
        # estimations which are based off peep_min
        ydelta = (data_cycle[-1][0] - data_cycle[-5][0])/5
        jump = int(0.05/ydelta)  # estimate index @ 0.05s for plotting
        peepi = data_cycle[-jump][1] - peep_min
        text = "PEEPi={:2.1f}".format(peepi)
        if plot:
            self.ax1.plot(data_cycle[-jump][0], data_cycle[-jump][1], "g*")
            self.ax1.text(data_cycle[-1][0], -5, text,
                     verticalalignment='bottom')

        # I:E ratio
        # 1:(expiration time)/(inspiration time)
        # expire from plateau to where peepi is measured
        exp1 =  data_cycle[-jump][0]-data_cycle[idx_min_start][0]
        # start of cycle to beginning of plateau
        ins1 =  data_cycle[idx_min_start][0]-data_cycle[0][0]
        denom = exp1 / ins1
        ie_text = "1:{:1.1f}".format(denom)
        if plot:
            self.ax1.text(data_cycle[int(peak_idx)][0], 0, ie_text,
                     verticalalignment='top')
            
        # Populate stats dictionary
        self.stats={} # initalize dict each time to avoid passing same reference to lists
        self.stats["PEEP"] = round(peep_min, 2)
        self.stats["PEEPi"] = round(peepi, 2)
        self.stats["Ppeak"] = round(peak, 2)
        self.stats["FlowI"] = round(data_cycle[peak_idx][0] - data_cycle[idx_max_start][0], 2)
        self.stats["Ipause"] = round(data_cycle[idx_min_start][0] - data_cycle[peak_idx][0], 2)
        self.stats["FlowE"] = round(data_cycle[idx_min_end][0] - data_cycle[idx_min_start][0], 2)
        self.stats["Epause"] = round(data_cycle[-1][0] - data_cycle[idx_min_end][0], 2)
        self.stats["I:E"] = ie_text
        self.stats["Pplat"] = round(data_cycle[idx_min_start][1], 2)
        self.stats["Start"] = round(self.data[start][0], 2)
        self.stats["End"] = round(self.data[end][0], 2)
        self.stats["Vt"] = 0      # not done
        self.stats["dP"] = round(data_cycle[idx_min_start][1] - peep_min, 2)
        self.stats["Pl"] = 0      # not done
        self.stats["P01"] = round(P01, 2)
        self.stats["PTP"] = round(PTPavg, 2)
        self.stats["RR"] = round((1 / (self.data[end][0] - self.data[start][0])) * 60, 2)
            
    def get_sample(self):
        """ Retrivies single sample from model """
        point = self.models.get_simulated_data()
        self.data.append(point)

    def read_pressure(self, seconds):
        """ Reads pressure data for specified number of seconds of data """
        self.get_sample()
        self.get_sample()
        # use data time frame for elapsed time, not realtime
        while (self.data[-1][0]-self.data[0][0]) < seconds:
            self.get_sample()
        return

    def track_breath(self, cycles=1, breath_number=0, timeout=10):
        """ Tracks breath cycles in real time
 
        Parameters:
        cycles (int): number of cycles (breaths) to track then analyze
        breath_number: absolute breath number to advance to
        timeout (int): seconds to search for pattern before aborting @TODO

        Returns:
        bool: returns 0 for failure, 1 for success, data is moved into self.data
        and self.cycle_stats
        """

        buffer = []
        sample_time = 0.0
        breath_cnt = 0
        state = 0  # no trigger

        # loop to sample data
        print("Sampling sensor {} cycles :: {} threshold"
              .format(cycles, self.threshold))
        while breath_cnt < cycles:   # no timeout yet
            # time.sleep(sample_rate)  # wait for sample - @TODO use RTC elapsed
            point = self.models.get_simulated_data()  # simulated
            buffer.append(point)

            # Test for threshold crossings
            if state == 0:
                # waiting for trigger positive
                if len(buffer) > 10 and breath_cnt == 0:
                    # slice of last 10 samples to try to place start cycle in
                    # same time window every so waveform looks triggered
                    buffer = buffer[-10:]
                if point[1] > self.threshold:
                    state = 1
                    continue
            if state == 1:
                # rising, wait for fall
                if point[1] < self.threshold:
                    state = 2
                    continue
            if state == 2:                # fallen, wait for start of next rise
                if point[1] > self.threshold:
                    state = 0
                    breath_cnt = breath_cnt + 1
        self.data = buffer
        self.compute()  # process samples
        return True

    def count_breaths(self, timeout=300, threshold=10):
        """ Counts breath cycles in data
 
        Parameters:
        timeout (int): seconds to search for pattern before aborting @TODO

        Returns:
        int: returns breath counts
        """

        breath_cnt = 0
        state = 0  # no trigger
        breath_markers = []
        samples = 0
        elapsed = time.time()
        self.threshold = threshold
        
        # loop to sample data
        while True:   # no timeout yet
            if (time.time() - elapsed) > timeout:
                print("Timed out {}s".format(timeout))
                break
            point = self.models.get_simulated_data()  # simulated
            samples += 1
            if point is None:
                print("Finished reading model data")
                break

            # Test for threshold crossings
            if state == 0:
                # waiting for trigger positive
                if point[1] > self.threshold:
                    state = 1
                    start = point[0]
                    continue
            if state == 1:
                # rising, wait for fall
                if point[1] < self.threshold:
                    state = 2
                    continue
            if state == 2:                # fallen, wait for start of next rise
                if point[1] > self.threshold:
                    state = 0
                    breath_cnt = breath_cnt + 1
                    breath_markers.append([start, point[0], breath_cnt])
        print("Samples = {} :: Threshold = {}".format(samples, self.threshold))
        print("Breaths counted = {}".format(breath_cnt))
        # print("Breath markers: {}".format(breath_markers))
        return breath_markers

    def find_irregular_cycles(self, markers, tol=25):
        """ Used for quick analysis to find irregular breaks in data 

            markers: [start, stop, breath_number] array to search for
            tol: percentage to bound time window by +/- tol%
        """

        avg_cycle = 0
        avg_gap = 0
        prev_end = 0
        for breath in markers:
            avg_cycle += (breath[1]-breath[0])
            avg_gap += breath[0]-prev_end
            prev_end = breath[1]
        avg_cycle /= len(markers)
        avg_gap /= len(markers)

        count = 0
        cycle = 0
        prev_end = 0
        flagged = []
        for breath in markers:
            count += 1
            cycle = (breath[1]-breath[0])
            gap = breath[0] - prev_end
            if (cycle > avg_cycle * (1 + tol/100)) or (cycle < avg_cycle * (1 - tol / 100)):
                # record some previous points before the trigger
                if count > 10:
                    flagged.append(markers[count-10])  # rewind for a few previous samples
                else:
                    flagged.append(breath)  # can't rewind yet
                
            #if (gap > avg_gap * 1.1) or (gap < avg_gap * 0.9):
            #    print("{}: gap {:1.2f}s vs avg {:1.2f}s".format(count, gap, avg_gap))
            prev_end = breath[1]
        return flagged

    def plot_cycle(self, markers, breath_number = 0, start = 0, cycles=5, length=500):
        """ Searches data file for either breath number or start time and grabs cycles
        of data and plots it and imports data for this captured section

        Uses: compute to calculate parameters on loaded cycles

        markers array [start, stop, breath number]
        breath_number int number to investigate, must match markers[breath_number]
        start float specify specific start time if desired otherwise taken from markers
        stop float specify when to stop reading data
        cycles int number of cycles to read from data
        """

        if breath_number != 0:
            idx = 0
            for i in range(0, len(markers)):
                # locate requested # in array
                if breath_number == markers[i][2]:
                    break
            idx = i
            start = markers[idx][0]
        if start == 0:
            start = markers[0][0] # pick first breath number if nothing specified
        self.models.rewind()  # reset model to start

        self.data = []
        self.datanp = []
        samples = 0
        slice = True
        #
        # @TODO this currently stores all data until time
        # is reached, this is unecessy and needs a lot of memory
        # need to prescreen data before appending to memory
        #
        while True:
            point = self.models.get_simulated_data()  # simulated
            samples += 1
            if point is None:
                print("Finished reading model data")
                break
            self.data.append(point)  # record data  @TODO fix later see above
            # Once triggered, slice off some leading data
            if point[0] >= start:
                if len(self.data)>10 and slice:
                    slice = False
                    # slice off all but previous 10 points
                    self.data=self.data[-10:]
            if len(self.data ) > length and slice == False:
                # started capturing waveform and done with points
                break

        title="Breath Number: {} [{}, {}]".format(markers[idx][2], markers[idx][0], markers[idx][1])
        # self.plot_diff(title=title)
        self.stats['BN'] = markers[idx][2] # record BN
        self.compute(plot=True, title=title)

    def print(self):
        i = 0
        for item in self.cycle_stats:

            print("Cycle #{}:".format(i))
            i += 1
            for key, value in item.items():
                print("{:>10} = {}".format(key, value))

                    
if __name__ == "__main__":

    file = '0-pres-c381f37ef559435eac162bd44904f412-rpi2-2141-11-28-07-59-42.014144.csv'
    filename = Path.cwd() / 'models' / 'csv_raw' / file

    mon = MONITOR2(str(filename))
    
    # mon.track_breath(cycles=2, max_peak=50)
    # mon.print()
    
    # test for long sample of time
    # mon.read_pressure(seconds=10)
    # mon.compute(plot=True)  # setting plot to true will show the data graph
    # mon.print()

    # test for breath patterns in data
    print("Scanning through {}".format(file))
    print("Looking for irregular breating intervals")
    print("CTRL-C to stop looping through data")
    
    markers = mon.count_breaths(timeout=300, threshold=14)
    irregs = mon.find_irregular_cycles(markers)
    for i in range(0, len(irregs)):
        print("{}: BN={} - {} irregs".format(i, irregs[i][2], irregs[i]))
        mon.plot_cycle(irregs, breath_number=irregs[i][2], length=300)
        mon.print()
