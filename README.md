# ventilator-parameters
Numerical model to simulate ventilator airway pressures and extract key parameters using simple methods that should not be too resource intensive. This code is non-optimized and is currently in a proof-of-concept testing stage.

This is a rapid prototype using python3 to process sample data from a differential pressure gauge and compute some of the values. This simulation is based on model data found on the internet and extracted to csv files. These models are setup to be scaled easily for peak, respiration rate, and peep values.

## licence
Licensed under GNU GPL-3. You have the freedom to do whatever with this code except distribute it in closed source versions.

# Model.py
model.py loads the selected numerical values from the ./models/ folder.  It can also scale and will simulate a live sensor. At this point no radomization has been added to the model, but it will be added soon. Also there are only two models, one well behaved and one with large peak vs. plateau values.

# Monitor.py
This performs all the sampling from model.py and will then parse, compute and display the results. It can be plotted using matplotlib or the results are printed to the console using pprint library.

## What does the code do?

* Measures the following signals:  
 * PEEP: PEEP pressure
 * PEEPi: Intrinsic PEEP presure
 * Ppeak: Peak pressure
 * FlowI: Inspiratory inflow time
 * Ipause: Inspiry pause time
 * FlowE: Expiratory flow time
 * Epause: Expiratory pause time
 * Pplat: Plateau Pressure
 * Start: start time of cycle
 * End: end time of cycle
 * Vt: tidal volume - @TODO - not measured
 * dP: driving pressure
 * Pl: transpulmonary pressure - @TODO - not computed yet
 * P01: Occlusion pressure
 * PTP: pressure-time product per breath cycle
 * RR: breaths per min. based on current cycle speed
* It can detect respiration cycles in the data automatically.
* Each cycle is parsed and analyzed separetly
* Parameters from each cycle is stored in a list of dictionaries for experimentation
* Models can be easily made and tested by changing the csv files found in the /models directory
* The plots are shown to aid in understanding the methods used to compute the parameters

# How to Run It
Just unzip or clone the repository.  You'll need matplotlib, numpy and pprint libraries (sorry no time for setup.py files, etc.).  For a test run just issue

python3 monitor.py

You can then modify the models or explore the calculations on your own. Feedback welcome, but the code is neither elegant or complete at this point.

# Urgency
Do the the current issues of Covid-19 and ARDS patients this code was rapidly put together and still needs much refactoring and alot of testing and work. The design of the code was specifically done to avoid complex python libraries and allow for fairly easy conversion to other languages and running on resource limitied processors. However due to the nature of writing fast code and quick testing there is a lot of fat that can be cut out.

# Documentation
All the documentation is embedded in the code for speed. There are a lot of array indices manipulation and shuffling to attempt to avoid too many complex operations, however the end result is a somewhat complex shuffling that is hopefuly called out in the code clearly.

# Example Test runs of monitor.py
Using ./models/b40-peep0-30s.csv

![model test](/snapshots/figure_1-2.png)

`Setting up model.
Model rate BPM = 30.0, Model Peak Pressure = 31.0 cm H2O
PEEP = 5.0, Sample window = 2.0
Sampling sensor for 7s
[{'End': 6.019999999999916,
  'Epause': 0.70999999999998487,
  'FlowE': 0.3799999999999919,
  'FlowI': 0.31999999999999318,
  'I:E': '1:1.2',
  'Ipause': 0.56999999999998785,
  'P01': 24.23155334686299,
  'PEEP': 5.0,
  'PEEPi': 0.0,
  'PTP': 25.648225443841262,
  'Pl': 0,
  'Ppeak': 30.989249380448868,
  'Pplat': 29.433065663545882,
  'RR': 30.150753768844865,
  'Start': 4.0299999999999585,
  'Vt': 0,
  'dP': 24.433065663545882},
 {'End': 6.019999999999916,
  'Epause': 0.70999999999998487,
  'FlowE': 0.3799999999999919,
  'FlowI': 0.31999999999999318,
  'I:E': '1:1.2',
  'Ipause': 0.56999999999998785,
  'P01': 24.23155334686299,
  'PEEP': 5.0,
  'PEEPi': 0.0,
  'PTP': 25.648225443841262,
  'Pl': 0,
  'Ppeak': 30.989249380448868,
  'Pplat': 29.433065663545882,
  'RR': 30.150753768844865,
  'Start': 4.0299999999999585,
  'Vt': 0,
  'dP': 24.433065663545882},
 {'End': 6.019999999999916,
  'Epause': 0.70999999999998487,
  'FlowE': 0.3799999999999919,
  'FlowI': 0.31999999999999318,
  'I:E': '1:1.2',
  'Ipause': 0.56999999999998785,
  'P01': 24.23155334686299,
  'PEEP': 5.0,
  'PEEPi': 0.0,
  'PTP': 25.648225443841262,
  'Pl': 0,
  'Ppeak': 30.989249380448868,
  'Pplat': 29.433065663545882,
  'RR': 30.150753768844865,
  'Start': 4.0299999999999585,
  'Vt': 0,
  'dP': 24.433065663545882}]`
  
  And model ./models/b40-peep0-30s.csv
  
  
![model test2](/snapshots/figure_1-1.png)
  
`Setting up model.
Model rate BPM = 30.0, Model Peak Pressure = 31.0 cm H2O
PEEP = 5.0, Sample window = 2.0
Sampling sensor for 7s
[{'End': 6.029999999999916,
  'Epause': 0.19999999999999574,
  'FlowE': 0.48999999999998956,
  'FlowI': 0.59999999999998721,
  'I:E': '1:0.5',
  'Ipause': 0.68999999999998529,
  'P01': 16.414433611064332,
  'PEEP': 5.0000000000001226,
  'PEEPi': 0.043954608760907732,
  'PTP': 23.973148658562014,
  'Pl': 0,
  'Ppeak': 30.962017960174403,
  'Pplat': 23.572380204505137,
  'RR': 30.150753768844865,
  'Start': 4.039999999999958,
  'Vt': 0,
  'dP': 18.572380204505016},
 {'End': 6.029999999999916,
  'Epause': 0.19999999999999574,
  'FlowE': 0.48999999999998956,
  'FlowI': 0.59999999999998721,
  'I:E': '1:0.5',
  'Ipause': 0.68999999999998529,
  'P01': 16.414433611064332,
  'PEEP': 5.0000000000001226,
  'PEEPi': 0.043954608760907732,
  'PTP': 23.973148658562014,
  'Pl': 0,
  'Ppeak': 30.962017960174403,
  'Pplat': 23.572380204505137,
  'RR': 30.150753768844865,
  'Start': 4.039999999999958,
  'Vt': 0,
  'dP': 18.572380204505016},
 {'End': 6.029999999999916,
  'Epause': 0.19999999999999574,
  'FlowE': 0.48999999999998956,
  'FlowI': 0.59999999999998721,
  'I:E': '1:0.5',
  'Ipause': 0.68999999999998529,
  'P01': 16.414433611064332,
  'PEEP': 5.0000000000001226,
  'PEEPi': 0.043954608760907732,
  'PTP': 23.973148658562014,
  'Pl': 0,
  'Ppeak': 30.962017960174403,
  'Pplat': 23.572380204505137,
  'RR': 30.150753768844865,
  'Start': 4.039999999999958,
  'Vt': 0,
  'dP': 18.572380204505016}]`
  
