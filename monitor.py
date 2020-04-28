#!/usr/bin/python3
"""
Monitor pressure and pull out key metrics

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
import model

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


class MONITOR:

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

    def __init__(self):
        print("Setting up model.")
        self.models = model.BREATH()
        self.scale_model()  # add in peep, bpm and peak pressure point

    def enable_random(self, random=[0, 0, 0]):
        self.random = random

    def scale_model(self, bpm=30, peak=31, peep=5):
        self.models.scale(bpm, peak, peep)
        self.threshold = peep * self.threshold_factor

    def plot(self):
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
        # waveform
        ax1.plot(yar, xar)
        plt.show()

    def compute(self, plot=True):
        """
        Computes parameters of all cycle samples in self.data
        """
        self.datanp = np.array(self.data)  # convert to numpy array quickly

        peak = np.amax(self.datanp, axis=0)  # peak value
        peak_idx = np.argmax(self.datanp, axis=0)  # index with peak value
        peep_min = np.amin(self.datanp, axis=0)  # peep value
        ave = np.average(self.datanp, axis=0)  # average of all data

        # convert to scalar from 2d array of [time, pressure]
        self.peak_idx = peak_idx[1]
        self.peep_min = peep_min[1]  # floor of pressure readings (PEEP)
        self.peak = peak[1]
        self.max_time = peak[0]

        if self.threshold == 0:
            threshold = self.peep_min * self.threshold_factor  # factor for trigger
        else:
            threshold = self.threshold

        self.threshold = threshold
        self.find_cycles(threshold)  # find start/end points of each cycle

        if plot:
            self.fig = plt.figure()

        for i in range(0, int(len(self.captured) / 2)):
            self.contours(i, threshold, plot)  # find points in cycle i
            self.cycle_stats.append(self.stats)  # build list of dictionary stats
        if plot:
            plt.ylim(bottom=-3)  # return the current ylim
            plt.show()

    def find_cycles(self, threshold):
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
        cycle = 0
        captured = []
        captured_idx = []
        for i in range(1, len(xar)):
            # Looking for patterns in Negative (N) and Positive (P) crossings
            # searching for sequence of N->P, P->N, N->P = full cycle
            if cycle == 0 and xar[i] < 0:
                # find first negative region N
                cycle = 1
            elif cycle == 1 and xar[i] > 0:
                # positive region N->P Found
                captured.append(self.data[i])  # start of inhalation
                captured_idx.append(i)  # index of event
                cycle = 2
            elif cycle == 2 and xar[i] < 0:
                cycle = 3  # start of pause P->N Found
            elif cycle == 3 and xar[i] > 0:
                # end of pause and start of next inhalation N->P
                captured.append(self.data[i])
                captured_idx.append(i)  # index of event
                cycle = 1
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
            # plot full waveform
            ax1 = self.fig.add_subplot(1, 1, 1)
            xar = self.data[:1]
            xar = []
            yar = []
            for eachLine in self.data:
                if len(eachLine) > 1:
                    x, y = eachLine[1], eachLine[0]
                    yar.append(float(y))
                    xar.append(float(x))

            # plot waveform - full dataset only on cycle 0
            if cycle == 0:
                ax1.plot(yar, xar)
                ax1.plot([yar[0], yar[-1]], [threshold, threshold], 'r:')
                ax1.text(yar[int(len(yar) / 2)], threshold, "Threshold {:1.1f}".format(threshold))
                for i in range(0, len(self.captured), 2):
                    ax1.text(self.captured[i][0], 0, "S")  # Start cycle
                    ax1.text(self.captured[i + 1][0],
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
        x0=0
        y0=0
        diff=[]
        for x,y in data_cycle:
            m=(y-y0)/(x-x0)
            x0=x
            y0=y
            diff.append(m)
        diff=np.array(diff)
 
        # Analyze derivative for slope changes
        # drop one y-axis point for plotting differential
        diff_max = np.amax(diff)  # max value
        diff_min = np.amin(diff)  # min value
        i = np.argmax(diff)  # index for max point (start inhalation)
        j = np.argmin(diff)  # index for min point (possible start exhalation)

        if plot:
            # show peak
            ax1.plot([data_cycle[peak_idx][0]], [peak], 'ro')
            ax1.text(data_cycle[peak_idx][0], peak * 1.02, "Peak {:2.1f}".format(peak))

            # Show differential crossings cycle
            yar.pop()    
            # ax1.plot(yar[start:end], diff)
            # ax1.plot([yar[start],yar[-1]], [0,0])  # reference crossings

        # Find end of rising inhalation
        # search between max diff and min diff point for slope changes
        # look for where the slope drops by a factor of the peak
        for x in range(i, j):
            if diff[x] < 0:  # look at points where slope starts to fall
                if diff[x] <= diff_min / factor:  # slope slows by this factor
                    break
        j = x  # this might now be the start of exhalation or peak decay

        if plot:
            ax1.plot([data_cycle[i][0], data_cycle[i][0]], [0, peak],
                     'r:')  # start of rise inhalation

        # search between max diff and min diff point for slope changes
        # look for where the slope drops by a factor of the peak
        for x in range(i, j):
            if diff[x] <= diff_max / factor:  # slope slows by this factor
                break
        j2 = x  # possible end of exhalation cycle

        if plot:
            ax1.plot([data_cycle[x][0], data_cycle[x][0]], [0, peak],
                     'r-')  # end of rise of inhalation

        # search after min diff point for slope changes
        # look for where the slope drops by a factor of the peak
        for x in range(j, len(data_cycle)):
            if diff[x] >= diff_min / factor:  # slope slows by this factor
                break
        diff_min_idx = x  # index of the end of the exhalation slope
        j2 = x

        ################################################################
        # Special Case: large peak causes false detection of exhalation
        #
        # Check remaining waveform for another minimum for sanity check
        ################################################################
        # move over few samples if possible from peak to start search
        x_spec = x  # bracket off remaining cycle from minimum
        if x + 10 < len(diff):
            x_spec = x + 10
        diff_min_special = np.amin(diff[x_spec:])
        diff_min_special_idx = np.argmin(diff[x_spec:]) + x_spec  # second dip found

        use_special_case = False
        # is it similar in magnitude? +/- 0.3
        if diff_min_special != 0 and diff_min_special != diff_min:
            if (diff_min / diff_min_special) < 1.3 and (diff_min / diff_min_special) > 0.7:
                use_special_case = True
                # could also add time window check to see Ppeak close or equal to Pplat

        # reverse from minimum and search for start of slope
        # by finding where slope drops by a factor of the peak
        for x in range(diff_min_special_idx, x_spec, -1):
            if diff[x] >= diff_min_special / factor:  # slope slows by this factor
                break
        diff_min_special_idx = x   # index of the end of the exhalation slope

        # look for where the slope drops by a factor of the peak
        for x in range(x_spec, len(data_cycle)):
            if diff[x] >= diff_min_special / factor:  # slope slows by this factor
                break
        diff_min_special_idx2 = x + x_spec  # index of the end of the exhalation slope

        if use_special_case:
            j = diff_min_special_idx
            j2 = diff_min_special_idx2

        # second minimum limit checks
        # will plot exhale lines to end of cycle if error occurs
        # this is for checking this condition and checking algorithm sanity
        if j>len(data_cycle):
            print("{} j too big".format(j))
            j=len(data_cycle) - 10
        if j2>len(data_cycle):
            print("{} j2 too big".format(j2))
            j2=len(data_cycle) - 1
            

        if plot:
            ax1.plot([data_cycle[j][0], data_cycle[j][0]], [0, peak],
                     'g:')  # second minium found -- start
            ax1.plot([data_cycle[j2][0], data_cycle[j2][0]], [0, peak],
                     'g-')  # second minium found -- end

        # Plot Plateau
        ax1.plot(data_cycle[j][0], data_cycle[j][1], 'r*')
        ax1.text(data_cycle[j][0], data_cycle[j][1], "Pplat {:2.1f}".format(data_cycle[j][1]))

        # inspiry time -- trigger time to peak time
        # self.datanp[peak_idx][0] - self.datanp[i][0]

        # inspiry pause time -- peak to start of fall at point j
        # self.datanp[j][0] - self.datanp[peak_idx][0]

        # expiratory flow time - start of fall to end of slope
        # self.datanp[j2][0] - self.datanp[j][0]

        # expiratory pause time
        # self.datanp[-1][0] - self.datanp[j2][0]

        # Find P01 100ms into inhalation
        # linear interpolation to find value
        P01 = np.interp(self.data[start][0] + 0.1,
                        data_cycle[:, 0], data_cycle[:, 1])
        if plot:
            ydelta = (self.data[start+4][0] - self.data[start][0])/5
            jump = int(0.1/ydelta)  # estimate index @ 0.1s for plotting
            ax1.plot([self.data[start+jump][0]], [P01], 'ro')
            ax1.text(self.data[start+jump][0], P01, "P0.1 {:2.1f}".format(P01))

        # Find PTP for cycle
        PTPavg = np.average(data_cycle[0:peak_idx], axis=0)[1]
        if plot:
            text = "PTP={:2.1f}".format(PTPavg)
            ax1.text(self.data[int(start+peak_idx/2)][0], peep_min, text,
                     verticalalignment='top')

        # I:E ratio
        nomin1 = (data_cycle[peak_idx][0] - data_cycle[i][0]) + (data_cycle[j][0] - data_cycle[peak_idx][0])
        denom1 =  (data_cycle[diff_min_idx][0] - data_cycle[j][0]) + (data_cycle[-1][0] - data_cycle[diff_min_idx][0])
        denom1 = denom1/nomin1
        ie_text = "1:{:1.1f}".format(denom1)
        if plot:
            ax1.text(self.data[int(start+peak_idx)][0], 0, ie_text,
                     verticalalignment='top')

        # PEEPi
        # end may not the best spot to use because it's the start
        # of the next inhalation cycle at the threshold point
        # Also high PEEPi values might interfere with threshold
        # estimations which are based off peep_min
        ydelta = (self.data[end][0] - self.data[end-4][0])/5
        jump = int(0.05/ydelta)  # estimate index @ 0.05s for plotting
        peepi = self.data[end-jump][1] - peep_min
        text = "PEEPi={:2.1f}".format(peepi)
        if plot:
            ax1.plot(self.data[end-jump][0], self.data[end-jump][1], "g*")
            ax1.text(self.data[end][0], -5, text,
                     verticalalignment='bottom')
            
        # Populate stats dictionary
        self.stats={} # initalize dict each time to avoid passing same reference to lists
        self.stats["PEEP"] = round(peep_min, 2)
        self.stats["PEEPi"] = round(peepi, 2)
        self.stats["Ppeak"] = round(peak, 2)
        self.stats["FlowI"] = round(data_cycle[peak_idx][0] - data_cycle[i][0], 2)
        self.stats["Ipause"] = round(data_cycle[j][0] - data_cycle[peak_idx][0], 2)
        self.stats["FlowE"] = round(data_cycle[j2][0] - data_cycle[j][0], 2)
        self.stats["Epause"] = round(data_cycle[-1][0] - data_cycle[j2][0], 2)
        self.stats["I:E"] = ie_text
        self.stats["Pplat"] = round(data_cycle[j][1], 2)
        self.stats["Start"] = round(self.data[start][0], 2)
        self.stats["End"] = round(self.data[end][0], 2)
        self.stats["Vt"] = 0      # not done
        self.stats["dP"] = round(data_cycle[j][1] - peep_min, 2)
        self.stats["Pl"] = 0      # not done
        self.stats["P01"] = round(P01, 2)
        self.stats["PTP"] = round(PTPavg, 2)
        self.stats["RR"] = round((1 / (self.data[end][0] - self.data[start][0])) * 60, 2)
            
    def get_sample(self, time):
        """ Retrivies single sample from model with specified time index """
        point = self.models.get_simulated_data(time, self.random)
        self.data.append([time, point])

    def read_pressure(self, seconds, delay=0.01):
        """ Reads pressure data for specified number of seconds """
        timer = 0  # time index in seconds
        delay = 0.010  # sample delay
        # loop to sample data
        print("Sampling sensor for {}s".format(seconds))
        while timer < seconds:
            time.sleep(delay)  # wait for sample
            self.get_sample(timer)
            timer = timer + delay

    def track_breath(self, cycles=1, timeout=10,
                     sample_rate=0.01, max_peak=35):
        """ Tracks breath cycles in real time
 
        Parameters:
        cycles (int): number of cycles (breaths) to track then analyze
        timeout (int): seconds to search for pattern before aborting @TODO
        sample_rate (float): seconds between pressure samples
        max_peak (float): if measured above this value generate alarm @TODO

        Returns:
        bool: returns 0 for failure, 1 for success, data is moved into self.data
        and self.cycle_stats
        """

        buffer = []
        sample_time = 0.0
        breath_cnt = 0
        state = 0  # no trigger

        # loop to sample data
        print("Sampling sensor {} cycles :: {} sample rate :: {} threshold"
              .format(cycles, sample_rate, self.threshold))
        while breath_cnt < cycles:   # no timeout yet
            time.sleep(sample_rate)  # wait for sample - @TODO use RTC elapsed
            point = self.models.get_simulated_data(sample_time, self.random)  # simulated
            buffer.append([sample_time, point])
            sample_time = sample_time + sample_rate

            if point > max_peak:
                print("ALERT! Max Pressure Limit Exceeded!")
                # @TODO
                # alarm UI and adjust motor mechanism if necessary

            # Test for threshold crossings
            if state == 0:
                # waiting for trigger positive
                if len(buffer) > 10 and breath_cnt == 0:
                    # slice of last 10 samples to try to place start cycle in
                    # same time window every so waveform looks triggered
                    buffer = buffer[-10:]
                if point > self.threshold:
                    state = 1
                    continue
            if state == 1:
                # rising, wait for fall
                if point < self.threshold:
                    state = 2
                    continue
            if state == 2:                # fallen, wait for start of next rise
                if point > self.threshold:
                    state = 0
                    breath_cnt = breath_cnt + 1
        self.data = buffer
        self.compute()  # process samples
        return True

    def print(self):
        i = 0
        for item in self.cycle_stats:
            print("Cycle #{}:".format(i))
            i += 1
            for key, value in item.items():
                print("{:>10} = {}".format(key, value))

                    
if __name__ == "__main__":
    mon = MONITOR()
    mon.enable_random(random=[10, 10, 10])  # note bpm randomness not working now
    
    #mon.track_breath(cycles=2, max_peak=50)
    #mon.print()
    
    # test for long sample of time
    mon.read_pressure(seconds=7, delay=0.01)
    mon.compute(plot=True)  # setting plot to true will show the data graph
    mon.print()
