#===================
# getECMWF.py 
#===================
"""
***meta***
The script gets ECMWF xml data for the supplied locations and converts it to csv format.

Current supplied locations:
Bear_Mnt       55.6986 -120.4306 
Dokie          55.8167 -122.2586 
Quality_Wind   55.1887 -120.8682 
Quality_Wind2  55.1887 -120.8682 
Cape_Scott     50.7655 -127.9954 


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
# january 2015


#-----------------INPUT--------------------------

stations = ['Bear_Mnt','Dokie','Quality_Wind','Quality_Wind2','Cape_Scott']
lat = [55.6986, 55.8167,55.1887,55.1887,50.7655]
lon = [-120.4306,-122.2586,-120.8682,-120.8682,-127.9954]
#msl = [0,0,0,0,0]

#flag to store precipitation
precip_flag = 1

#choose which vars and attributes to import (see sample list above). MUST BE THE SAME LENGTH
var_names = ['temperature', 'windDirection','windSpeed','humidity','pressure','cloudiness',\
			'fog','lowClouds','mediumClouds', 'highClouds','dewpointTemperature']
var_attr = ['value','deg','mps','value','value','percent','percent','percent','percent','percent','value']

#make a list of units for above vars (see meta above)
var_units = ['(c)','(deg)','(mps)','(pcnt)','(hPa)','(pcnt)','(pcnt)','(pcnt)','(pcnt)','(pcnt)','(c)']

data_dir = '/Users/nmoisseeva/data/ECMWF/'

#-------------end of input-----------------------

import urllib2
import numpy as np
from matplotlib import pyplot as plt
import sys, os
import datetime
from xml.etree import ElementTree as etree
import csv


#test that all stations have lat/lon/msl information
if len(stations) != len(lat) or len(stations) !=  len(lon):
	sys.exit('Please ensure that latitude/longitute information is complete for all stations')


#test that the number of variables matches number of attributes and units
if len(var_names) != len(var_attr) or len(var_names) != len(var_units):
	sys.exit('Please ensure that var_names, var_attr and var_units are the same length')

# #create storage folders for data (if they don't yet exist)
# for nStn, stn in enumerate(stations):
# 	stn_path = data_dir + stn + '/'
# 	if not os.path.exists(stn_path):
# 		print('Creating storage directory: ' + stn_path)
# 		os.makedirs(stn_path)


#loop through all supplied stations to get xml data
for nStn, stn in enumerate(stations):
	url = 'http://api.yr.no/weatherapi/locationforecast/1.9/?lat=' + str(lat[nStn]) + ';lon=' + str(lon[nStn]) + ';'
	load = urllib2.urlopen(url)
	contents = load.read()
	xmlfile = stn + '.xml'
	file = open(xmlfile, 'w')
	file.write(contents)
	file.close()
	if os.path.exists(xmlfile):
		print('XML donwload complete for ' + stn + ' station. ' + str(datetime.datetime.now()))


#loop through all supplied stations to convert xml to csv
print('Converting XML files to CSV -------->')
for nStn, stn in enumerate(stations):
	xmlfile = stn + '.xml'
	print("...converting " + xmlfile)
	tree = etree.parse(xmlfile)													#get xml tree structure
	meta = tree.find('.//model')												#find metadata
	meta_time = meta.attrib['termin']											#get the model run start - will become file id
	print('Model run start time: '+ meta_time)
	run_dt = datetime.datetime.strptime(meta_time, '%Y-%m-%dT%H:%M:%SZ')		#convert to datetime object
	timestamp = tree.findall('.//time') 										#find all time stamps present in file
	

	#deal with precipitation separately
	if precip_flag==1:
		csvname_p = 'precip' + run_dt.strftime('%Y-%m-%d_%H%M') + '_' + stn + '.csv'		#create precip filename from datetime
		prp_cnt = len(tree.findall('.//precipitation'))							#count all precipitation elements
		csvopen_p = open(csvname_p,'w')											#setup csv file for writing
		csvwrite_p = csv.writer(csvopen_p)
		csvwrite_p.writerows([['from','to','precipitation (mm)']])				#write header row
		rec_cnt_p = 0															#record counter for sanity check
		for nPrp, item in enumerate(timestamp):
			precip_val = item.find('.//precipitation')							#check that time element has precipitation child
			if precip_val is not None:											
				data_row = [[item.attrib['from'], item.attrib['to'], precip_val.attrib['value']]]	
				csvwrite_p.writerows(data_row)									#write a row [start, end, value (mm)]
				rec_cnt_p = rec_cnt_p + 1 										#add counter each time a row is written
		csvopen_p.close()

		if rec_cnt_p == prp_cnt:												#sanity check: count records and rows
			print('Total number of precipitation records found: ' + str(prp_cnt))
		else:
			print('WARNING: Mismatch between nubmer of records and timestamps. [stamps: ' + str(prp_cnt) + ', vals: ' + str(rec_cnt_p) + ']')

		#save csv file in appropriate directory
		save_path = data_dir + stn + '/' + str(run_dt.year) + '/' + str(run_dt.month) + '/' + csvname_p
		os.renames(csvname_p, save_path)
		print('Moving file %s to directory %s' %(csvname_p, save_path) )

	#now write the main data file
	csvname = run_dt.strftime('%Y-%m-%d_%H%M') + '_' + stn + '.csv'				#generate filename
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
		rec_cnt = rec_cnt + 1 													#add counter
		if len(data_row) == len(var_names) + 1: 								#check that no data is missing
			csvwrite.writerows([data_row])										#if all data is present write wrote to csv
	csvopen.close()																#close csv
	print("Total number of records stored for each variable: " + str(rec_cnt))

	#save csv file in appropriate directory
	save_path = data_dir + stn + '/' + str(run_dt.year) + '/' + str(run_dt.month) + '/' + csvname
	os.renames(csvname, save_path)
	print('Moving file %s to directory %s ' %(csvname, save_path))

print('======================COMPLETE========================')








