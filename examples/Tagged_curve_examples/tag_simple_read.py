"""
This simple example reads data from a TAGGED curve
Have a look at the documentation for further information:
"""
import volue_insight_timeseries
import pandas as pd
import matplotlib.pyplot as plt

############################################
# Insert the path to your config file here!
my_config_file = 'path/to/your/config.ini'
############################################


# Create a session to Connect to Volue Insight API
session = volue_insight_timeseries.Session(config_file=my_config_file)

# Define start and end time
# start_date
start_date = pd.Timestamp('2018-6-1 00:00')
# end_date
end_date =  pd.Timestamp('2018-6-8 00:00')

# define curve name to read, in this case ???????
curve_name = 'WE NEED TO FIND A CURVE HERE'
# get the curve
curve = session.get_curve(name=curve_name)

# Get the available tags for this curve and print them
tags = curve.get_tags()
print('\n###\nAvailable tags for this curve:\n', tags)

# read curve data for tag='01' from start_date to end_date to ts object
ts = curve.get_data(tag='01', data_from=start_date, data_to=end_date)
# convert to pandas.Series object
s = ts.to_pandas()


# plot curve using the integrated plot function of pandas
s.plot()
# show the figure
plt.show()
