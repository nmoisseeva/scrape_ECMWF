#===================
# getECMWF.py 
#===================
"""
***meta***
The script gets ECMWF xml data for the supplied locations and converts it to csv format.

Sample raw data from XML file:
            <temperature id="TTT" unit="celsius" value="3.3"/>
            <windDirection id="dd" deg="243.4" name="SW"/>
            <windSpeed id="ff" mps="4.4" beaufort="3" name="Lett bris"/>
            <humidity value="71.7" unit="percent"/>
            <pressure id="pr" unit="hPa" value="1004.8"/>
            <cloudiness id="NN" percent="100.0"/>
            <fog id="FOG" percent="0.0"/>
            <lowClouds id="LOW" percent="0.0"/>
            <mediumClouds id="MEDIUM" percent="88.3"/>
            <highClouds id="HIGH" percent="100.0"/>
            <dewpointTemperature id="TD" unit="celsius" value="0.1"/>

"""
# nmoisseeva@eos.ubc.ca
# february 2016


#-----------------INPUT--------------------------

#config directory
cfg_file = '/nfs/crypt/arena/users/model/setup/wpVerif2.cfg'

#choose which vars and attributes to import (see sample list above). MUST BE THE SAME LENGTH
var_names = ['windSpeed']
var_attr = ['mps']

#make a list of units for above vars (see meta above)
var_units = ['(mps)']

#directory for saving data
data_dir = '/nfs/neltharion/www/results/ECMWF/'

#-------------end of input-----------------------

import urllib2
import numpy as np
from matplotlib import pyplot as plt
import sys, os
import datetime
from xml.etree import ElementTree as etree
import csv


#stations = ['Bear_Mnt','Dokie','Quality_Wind','Quality_Wind2','Cape_Scott']
stations = list(np.genfromtxt(cfg_file,dtype=str,usecols=0))
lat = list(np.genfromtxt(cfg_file,dtype=float,usecols=1))
lon = list(np.genfromtxt(cfg_file,dtype=float,usecols=2))

#test that all stations have lat/lon/msl information
if len(stations) != len(lat) or len(stations) !=  len(lon):
	sys.exit('Please ensure that latitude/longitute information is complete for all stations')


#test that the number of variables matches number of attributes and units
if len(var_names) != len(var_attr) or len(var_names) != len(var_units):
	sys.exit('Please ensure that var_names, var_attr and var_units are the same length')

#loop through all supplied stations to get xml data
for nStn, stn in enumerate(stations):
	url = 'http://api.yr.no/weatherapi/locationforecast/1.9/?lat=' + str(lat[nStn]) + ';lon=' + str(lon[nStn]) + ';'
	load = urllib2.urlopen(url)
	contents = load.read()
	xmlfile = './run/'+ stn + '.xml'
	file = open(xmlfile, 'w')
	file.write(contents)
	file.close()
	if os.path.exists(xmlfile):
		print('XML donwload complete for ' + stn + ' station. ' + str(datetime.datetime.now()))


#loop through all supplied stations to convert xml to csv
print('Converting XML files to CSV -------->')
for nStn, stn in enumerate(stations):
	xmlfile = './run/'+ stn + '.xml'
	print("...converting " + xmlfile)
	tree = etree.parse(xmlfile)													#get xml tree structure
	meta = tree.find('.//model')												#find metadata
	meta_time = meta.attrib['termin']											#get the model run start - will become file id
	print('Model run start time: '+ meta_time)
	run_dt = datetime.datetime.strptime(meta_time, '%Y-%m-%dT%H:%M:%SZ')		#convert to datetime object
	timestamp = tree.findall('.//time') 										#find all time stamps present in file
	
	#now write the main data file
	run_timestamp = run_dt.strftime('%Y-%m-%d_%H%M')
	csvname = './run/'+ run_timestamp + '_' + stn + '.csv'				#generate filename
	csvopen = open(csvname,'w')          										#setup csv for writing
	csvwrite = csv.writer(csvopen)
	header = ['Timestamp'] + [ var_names[i] + var_units[i] for i in range(len(var_names))]	#create a header row
	csvwrite.writerows([header])												#write header row
	rec_cnt = 0																	#setup counter
	for nRec, fcst in enumerate(timestamp):										#loop through available timesteps
		data_row = []
		for nVar, var in enumerate(var_names):									#loop through required variables
			child_call = './/' + var 											#generate search argument
			get_var = fcst.find(child_call)										#get instance of variable
			if get_var is not None:												#check that record exists
				data_row.extend([get_var.attrib[var_attr[nVar]]])				#append row with new daata
		data_row = [fcst.attrib['from']] + data_row								#add time step at the beginning of the row	
		if len(data_row) == len(var_names) + 1: 								#check that no data is missing
			csvwrite.writerows([data_row])										#if all data is present write wrote to csv
			rec_cnt = rec_cnt + 1 													#add counter

	csvopen.close()																#close csv
	print("Total number of records stored for each variable: " + str(rec_cnt))

	#save csv file in local directory
	save_path = './run/' + run_timestamp + '_' + stn + '.csv'
	os.renames(csvname, save_path)
	print('Saving individual station file %s to directory %s ' %(csvname, save_path))

#construct a Wind Hub file from existing station files 							#create storage array for all stations
WND_HUB = np.empty((rec_cnt,len(stations)+1)) * np.nan
for nStn, stn in enumerate(stations):
	stnfile = './run/'+ run_timestamp + '_' + stn + '.csv' 						#generate filename
	#if on first stsation - extract forecast horizon
	if nStn==0:
		fcsthr = np.genfromtxt(stnfile,usecols=0,dtype=str,skip_header=1,delimiter=',') 	#for first run record forecast horizons
		if len(fcsthr)!=(rec_cnt):
			print('WARNING: mismatch in number of records between stations. Requires manual verification!!!') #check that all files are the same
		delt = [datetime.datetime.strptime(fcsthr[i], '%Y-%m-%dT%H:%M:%SZ') - run_dt for i in range(rec_cnt)] #calculate time offset
		offset = [int(delt[i].days * 24. + delt[i].seconds /3600.) for i in range(rec_cnt)] 					#convert to hours
		WND_HUB[:,0] = offset 													#store offset
	WND_HUB[:,nStn+1] = np.genfromtxt(stnfile,usecols=1,skip_header=1,delimiter=',') 		#store wind data for all stations


#save csv file in appropriate directory
save_path = data_dir + run_dt.strftime('%y%m%d%H')  + '/ASCII/m/g3/WND_HUB.1.t'
row_format = ['%d'] + (['%f' for i in range(len(stations))])
np.savetxt(save_path,WND_HUB,fmt=row_format, delimiter=' ')
print('Saved wind hub file to directory %s ' %save_path)

os.mknod(data_dir + run_dt.strftime('%y%m%d%H')  + '/ASCII/m/g3/WND_HUB.1.t.OK')

print('======================COMPLETE========================')








