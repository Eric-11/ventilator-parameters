#!/usr/bin/python3
"""
Convert Ventmode data into cvs flow, pressure csv
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
import glob
import os
from pathlib import Path
import argparse


class Convert:
    def __init__(self):
        # get file list and convert
        i = 0
        glob_path = Path.cwd() / 'raw_vwd'
        for name in glob_path.rglob("*.csv"):
            print("Converting {}".format(name.name))
            self.process(in_file=name, o_file=i)
            i += 1
        print("{} Files processed".format(i))

    def process(self, in_file='', o_file=''):
        try:
            name = in_file.name
            fp_in = open(str(in_file), "r",
                         errors='ignore')  # added ignore for unicode issues
            name1 = str(Path.cwd() / 'csv_raw' /
                        "{}-pres-{}".format(o_file, name))
            name2 = str(Path.cwd() / 'csv_raw' /
                        "{}-flow-{}".format(o_file, name))
            fp_out_pres = open(name1, "w")
            fp_out_flow = open(name2, "w")
        except Exception as e:
            print("unable to open: " + str(e))
            exit()
        count = 0
        while True:
            try:
                line = fp_in.readline()
            except UnicodeDecodeError:
                print("Decode Error -- Abort. Line count {}:{}".format(
                    count, line))
                break
            x = line.split(", ")
            if not line:
                break
            if len(x) < 2:
                continue
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
                continue  # ignore it
            # Assume a 50hz sample time based on specs.
            # this is not entirely accurate because it's possible
            # samples are missing
            time_sample = count * 1 / 50  # 50hz sample time
            fp_out_pres.write("{},{}\n".format(time_sample, x[1]))
            fp_out_flow.write("{},{}\n".format(time_sample, x[0]))
            count += 1
        fp_in.close()
        fp_out_pres.close()
        fp_out_flow.close()


if __name__ == "__main__":
    print("You can get the raw_vmd ventilator data from:")
    print(
        "https://github.com/hahnicity/ventmode/tree/master/anon_test_data/raw_vwd"
    )
    print("Place this in a subdirectory raw_vwd")
    print("Make a subdirectory called csv_raw for the converted files")
    print("Run this script from the parent of these two directories")
    parser = argparse.ArgumentParser(
        description=
        'Convert all raw_vmd files and put them into cvs_raw pressure and flow data',
        epilog='Run in partent directory to raw_vwd and csv_raw')
    con = Convert()
