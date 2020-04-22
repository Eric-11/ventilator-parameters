CSV data for models. They are sampled from data found on the internet.

They are in seconds and cm H2O. If anyone has more csv or images of respiration that could share it would be very helpful to the robustness of our project.  They can also be in the form of an image and I can digitize the data and extract a csv version for my model.

/cvs_raw contains anonymous respirator data of flow and pressure from https://github.com/hahnicity/ventmode

#convert.py

Convert.py will remove some of the text inserted into the the ventilator waveform data saved by the ventilator.

Get the /raw_vmd files from https://github.com/hahnicity/ventmode/tree/master/anon_test_data/raw_vwd, create an empty csv_raw folder and run convert.py.  It will find all the file in /raw_vmd and convert and save them into /csv_raw
