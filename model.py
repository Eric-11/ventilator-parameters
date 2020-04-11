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


class BREATH:

    breath = ''
    bps = 0
    peak = 0
    peep_min = 0
    max_time = 0  # length of cycle
    filename = ''

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

    def scale(self, bpm=20, peak=30, peep=10):
        self.load(self.filename)  # reload unscaled and shifted model
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

    def contours(self):
        """
        computes assents, dessents and plateaus in wave form
        """
        max = np.amax(self.breath, axis=0)
        max_idx = np.argmax(self.breath, axis=0)
        min = np.amin(self.breath, axis=0)
        ave = np.average(self.breath, axis=0)
        self.min = min[1]  # floor of pressure readings (PEEP)
        self.bps = 1 / max[0]  # bps  - data has one breath
        self.peak = max[1]
        self.max_time = max[0]
        print("Model rate BPM = {:2.1f}, Model Peak Pressure = {:2.1f} cm H2O".
              format(self.bps * 60, self.peak))
        print("PEEP = {:2.1f}, Sample window = {:2.1f}".format(
            self.min, self.max_time))
        print("Average = {:2.1f}".format(ave[1]))

        diff = np.diff(self.breath[:, 1])
        gradient = np.sign(diff)

        fig = plt.figure()
        ax1 = fig.add_subplot(1, 1, 1)

        xar = []
        yar = []
        for eachLine in self.breath:
            if len(eachLine) > 1:
                y = eachLine[0]
                yar.append(float(y))
        # waveform
        ax1.plot(yar, self.breath[:, 1])

        # average
        ax1.plot([yar[0], yar[-1]], [ave[1], ave[1]], 'r--')

        # max point
        i = np.argmax(self.breath, axis=0)
        ax1.plot([self.breath[i[1]][0]], [max[1]], 'ro')
        ax1.text(self.breath[i[1]][0], max[1] * 1.02, "Peak")
        # boundary around peak
        # ax1.plot([yar[0], yar[-1]], [max[1] * 1.05, max[1] * 1.05], 'b--')
        # ax1.plot([yar[0], yar[-1]], [max[1] * 0.95, max[1] * 0.95], 'g--')

        # drop one y-axis point for plotting differential
        yar.pop()
        ax1.plot(yar, diff)
        diff_max = np.amax(diff)
        diff_min = np.amin(diff)
        i = np.argmax(diff)  # finds index for max point
        j = np.argmin(diff)  # finds index for min point
        ax1.plot([yar[i], yar[i]], [0, max[1]], 'p-')  # start of rise
        ax1.plot([yar[j], yar[j]], [0, max[1]], 'y-')  # start of fall
        ax1.text(yar[j], self.breath[j][1], "Plateau")

        # search between max diff and min diff point for slope changes
        # look for where the slope drops by a factor of the peak
        for x in range(i, j):
            if diff[x] <= diff_max / 5:  # slope slows by this factor
                break
        diff_max_idx = x
        ax1.plot([yar[x], yar[x]], [0, max[1]], 'p-')  # end of rise

        # search after min diff point for slope changes
        # look for where the slope drops by a factor of the peak
        for x in range(j, len(yar)):
            if diff[x] >= diff_min / 5:  # slope slows by this factor
                break
        diff_min_idx = x
        ax1.plot([yar[x], yar[x]], [0, max[1]], 'y-')  # end of rise

        # inspiry time
        print(max)
        print("Inspiratory flow time: {:2.1f} s".format(yar[max_idx[1]] -
                                                        yar[i]))
        # inspiry time
        print("Inspiry pause time: {:2.1f} s".format(yar[j] - yar[max_idx[1]]))
        # expiratory flow time
        print("Expiratory flow time: {:2.1f} s".format(yar[diff_min_idx] -
                                                       yar[j]))

        plt.show()

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

    def get_simulated_data(self, time):
        """
        Returns simulated reading from sensor
        time is in seconds and will be scaled to fit data model timeframe.
        Data returned is linearly interpolated for any time value and
        will roll over to beginning of the model automatically.
        """

        time = time % self.max_time  # scale to data model time
        xinterp = np.interp(time, self.breath[:, 0], self.breath[:, 1])
        return xinterp


if __name__ == "__main__":
    br = BREATH()
    br.plot_breath()
    br.scale()
    br.plot_breath()
    br.get_simulated_data(1)
