#!/usr/bin/python3
"""
Generates numerical model for breath to simulate sensor data
Data is modeled in a [time, pressure] 2d array
Raw waveform models can be found in the ./models directory.


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

from numpy import genfromtxt
import numpy as np
import matplotlib.pyplot as plt
from random import uniform
import time


class BREATH:

    breath = ''
    bps = 0
    peak = 0
    peep_min = 0
    max_time = 0  # length of cycle
    filename = ''

    # simulated values
    bps_sim = 0
    peak_sim = 0
    peep_sim = 0
    prev_sample = 0

    def __init__(self, filename="./models/b30-peep0-20s-lowpeak.csv"):
        # csv file with one cycle to be used for simulations
        # models should have the floor at 0 to make adding peep easy
        # ./models/b30-peep0-20s-lowpeak.csv   - low peak long pause
        # ./models/b40-peep0-30s.csv
        self.load(filename)

    def load(self, filename):
        self.breath = genfromtxt(filename, delimiter=',')
        self.filename = filename
        max = np.amax(self.breath, axis=0)
        min = np.amin(self.breath, axis=0)
        self.peep_min = min[1]  # floor of pressure readings (PEEP)
        self.bps = 1 / max[0]  # bps  - data has one breath
        self.peak = max[1]
        self.max_time = max[0]

    def scale(self, bpm=20, peak=30, peep=10, regenerate=False):
        """
        scale model waveform

        bpm (float): breaths per minute
        peak(float): cm h20 peak pressure
        peep(float): cm h20 peep pressure
        regenerate(bool): set true if updating a running sample in progress
        """

        self.load(self.filename)  # reload unscaled and shifted model

        # only store inital setup values
        # if calling to rescale or randomize set regenerate=true
        if not regenerate:
            self.bpm_sim = bpm
            self.peak_sim = peak
            self.peep_sim = peep

        i = 0
        bps = bpm / 60
        peak = peak - peep

        for eachLine in self.breath:
            self.breath[i] = [
                self.breath[i, 0] * self.bps / bps,
                (self.breath[i, 1]) * peak / self.peak + peep
            ]
            i = i + 1

        max = np.amax(self.breath, axis=0)
        self.bps = 60.0 / max[0]
        self.peak = max[1]
        self.min = peep
        self.max_time = max[0]
        print("Model rate BPM = {:2.1f}, Model Peak Pressure = {:2.1f} cm H2O".
              format(self.bps, self.peak))
        print("PEEP = {:2.1f}, Sample window = {:2.1f}".format(
            self.min, self.max_time))

    def plot_breath(self):

        fig = plt.figure()
        ax1 = fig.add_subplot(1, 1, 1)

        xar = []
        yar = []
        for eachLine in self.breath:
            if len(eachLine) > 1:
                x, y = eachLine[0], eachLine[1]
                xar.append(float(x))
                yar.append(float(y))
        ax1.plot(xar, yar)
        plt.show()

    def get_simulated_data(self, time, random=[0, 0, 0]):
        """
        Returns simulated reading from sensor
        time is in seconds and will be scaled to fit data model timeframe.
        Data returned is linearly interpolated for any time value and
        will roll over to beginning of the model automatically.

        time is in seconds, just so the model knows where in the waveform
        to provide a sample.

        random is the percentage of [bpm, peak, peep] to randomize after
        breath cycle. bpm is breaths per minute, peak is the peak pressure
        and peep is the positive end exhalation pressure.
        random = [bpm, peak, peep] for example:
        random = [5,1,3] would be a 5% variation in bpm, 1% in peak and
        3% in peep value.

        NOTE: random bpm is not working now because the changes in sample 
        window need to be padded to avoid discontinuities.

        The sample cycle may lag when a new waveform is generated.
        """
        if (time // self.max_time) > (self.prev_sample // self.max_time):
            if not (all(x == 0 for x in random)):
                # *** SCALING BPM doesn't work right now because it ***
                # *** Causes discontinuities in the waveform due to ***
                # *** model and sample time missmatches -- padding  ***
                # *** needed to make this work                      ***
                #bpm = uniform(self.bpm_sim * (1 - random[0] / 100),
                #              self.bpm_sim * (1 + random[0] / 100))
                bpm = self.bpm_sim
                pk = uniform(self.peak_sim * (1 - random[1] / 100),
                             self.peak_sim * (1 + random[1] / 100))
                peep = uniform(self.peep_sim * (1 - random[2] / 100),
                               self.peep_sim * (1 + random[2] / 100))
                self.scale(bpm, pk, peep, regenerate=True)

        sample = time % self.max_time  # scale to data model time
        xinterp = np.interp(sample, self.breath[:, 0], self.breath[:, 1])
        self.prev_sample = time  # track last point
        return xinterp


if __name__ == "__main__":

    seconds = 9
    delay = 0.010  # sample delay
    timer = 0
    data = []

    br = BREATH()
    br.scale()

    # loop to sample data
    print("Sampling sensor for {}s".format(seconds))
    while timer < seconds:
        time.sleep(delay)  # wait for sample
        data.append([timer, br.get_simulated_data(timer, random=[0, 10, 10])])
        timer = timer + delay
    fig = plt.figure()
    ax1 = fig.add_subplot(1, 1, 1)

    xar = []
    yar = []
    for eachLine in data:
        if len(eachLine) > 1:
            x, y = eachLine[0], eachLine[1]
            xar.append(float(x))
            yar.append(float(y))
    ax1.plot(xar, yar)
    plt.show()
