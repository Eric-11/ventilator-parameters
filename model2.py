#!/usr/bin/python3
"""
Model uses long sample runs from recorded
ventilator data. For now it only works with converted
csv data that has format of:

time,value

Currently only models pressure waveforms
"""
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import argparse
import time


class BREATH2:

    fp = ''
    type = ''
    raw_file = False
    point = 0

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

    def get_simulated_data(self):
        """
        Returns data from recorded cvs file until end of file
        [time, value]
        """
        data = self._get_data()
        return data

    def rewind(self):
        self.fp.seek(0)

    def _get_data(self):
        """ routine extract data from file"""

        data_bad = True
        while data_bad:
            try:
                line = self.fp.readline()
            except UnicodeDecodeError:
                print("Decode Error -- Abort")
                return

            if len(line) == 0:
                # end of file
                return

            x = line.split(",")

            if len(x) < 2:
                x = line.split(",")

            if len(x) < 2:
                print("META: {}".format(line), end='')
                if self.points == 0:
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
            self.points += 1
            time = self.points / 50
        else:
            p = x[1]
            time = x[0]
        self.prev_sample = time
        self.prev_value = p
        return [time, p]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Model raw_vmd or cvs_raw pressure or flow data',
        epilog='Demonstration of data plots')
    parser.add_argument('file', type=str, help="Input Filename with path")
    args = parser.parse_args()
    type = 'press'

    model = BREATH2(filename=args.file, type=type)

    elapsed = time.time()
    while True:
        data = model.get_simulated_data()
        delay = data[0] - (time.time() - elapsed)
        if delay > 0:
            time.sleep(delay)  # print in time close to samples
        print(data)
