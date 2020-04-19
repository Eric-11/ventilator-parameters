#!/usr/bin/python3
"""
Plots either raw_vmd or csv_raw files.
"""
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import argparse


class PlotData:
    ax = ''
    bins = ''
    limit = 500
    y_limit = 30
    fp = ''
    value = ''
    type = ''
    raw_file = False

    def __init__(self, filename='', type='press'):
        """
        Init plot class
        :param filename: input filename in csv format
        :param type: press is to plot the pressure, flow to plot flow rates
        """
        try:
            self.fp = open(filename, "r", errors='ignore')
        except IOError:
            print("Problem with IO")
            print("File {}: does not exist".format(filename))
            exit(1)
        self.type = type

    def plot(self):
        """ continuous plot of specified channel """
        matplotlib.use('tkagg')
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots()
        plt.xlim(0, self.limit)
        if self.type == 'press':
            plt.title("Pressure")
            plt.ylabel("cm H2O")
            plt.ylim(0, self.y_limit)
            self.cursor, = self.ax.plot([0, 0], [0, self.y_limit], color=(0.4, 1., 0.))
        else:
            plt.title("Flow")
            plt.ylabel("ml/s ?")
            plt.ylim(-self.y_limit, self.y_limit)
            self.cursor, = self.ax.plot([0, 0], [-self.y_limit, self.y_limit], color=(0.4, 1., 0.))

        self.bins = np.linspace(0, self.limit - 1, self.limit)
        self.value = [0] * self.limit
        self.line, = self.ax.plot(self.bins, self.value, 'r-')

        ani = animation.FuncAnimation(self.fig, self.animate, interval=50)
        plt.show()

    def animate(self, i):
        """ routine to animate plot sweep """
        item = i
        i = i % self.limit

        data_bad = True
        count = 0
        while data_bad:
            try:
                line = self.fp.readline()
            except UnicodeDecodeError:
                print("Decode Error -- Abort")
                return
            count += 1

            x = line.split(",")
            if len(x) < 2:
                x = line.split(",")

            if len(x) < 2:
                print("META: {}".format(line), end='')
                if item == 0:
                    self.raw_file = True
                continue
            else:
                data_bad = False

            x[1] = x[1].rstrip()
            try:
                x[0] = float(x[0])
                x[1] = float(x[1])
            except ValueError:
                # Meta data
                #
                # is it one of the following?
                # Time stamp
                # {year}-{month}-{day}-{hour}-{minute}-{second}.{millis}
                # 2192-07-15-04-43-37.103707
                #
                # Breath Start, S:<Breath Number>,
                # BS, S:2244,
                #
                # Breath End
                # BE
                self.raw_file = True
                data_bad = True
                continue
            data_bad = False


        if self.raw_file:
            if self.type == 'press':
                p = x[1]
            else:
                p = x[0]
        else:
            p = x[1]

        if p > self.y_limit:
            self.y_limit = int(p * 1.5)
        if p < -1 * self.y_limit:
            self.y_limit = abs(int(p * 1.5))

        if self.type == 'press':
            plt.ylim(0, self.y_limit)  # rescale bigger
            self.cursor.set_data([i, i], [0, self.y_limit])  # move cursor line
        else:
            plt.ylim(-self.y_limit, self.y_limit)  # rescale bigger
            self.cursor.set_data([i, i], [-self.y_limit, self.y_limit])  # move cursor line

        self.value[i] = p
        self.line.set_data(self.bins, self.value)  # update the data.
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot raw_vmd or cvs_raw pressure or flow data',
                                     epilog='Demonstration of data plots')
    parser.add_argument('-p', action='count', default=0, help='plot pressure')
    parser.add_argument('-f', action='count', default=0, help='plot flow rate')
    parser.add_argument('file', type=str, help="Input Filename with path")
    args = parser.parse_args()
    type = 'press'
    if args.f > 0:
        type = 'flow'
    if args.p > 0:
        type = 'press'

    convert = PlotData(filename=args.file, type=type)
    convert.plot()
