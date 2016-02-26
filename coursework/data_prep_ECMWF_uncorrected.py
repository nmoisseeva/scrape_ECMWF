'''
==================data_prep_ECMWF.py=====================
Script produces timeseries from ECMWF data for specified range and variable.
-currentlly works for single variable only

Plotting:
-timeseries
-power spectrum


'''

import numpy as np
from matplotlib import pyplot as plt
import sys, os
import datetime
import csv
from scipy import fft, arange, stats



#===========================input=============================
raw_dir = '/Users/nadya2/data/ECMWF/'
verif_dir = '/Users/nadya2/data/coursework/'
comps_data_dir = '/Users/nadya2/Applications/Comps-master/input/'
date_range = ['29012015', '21042015']
stations = ['Bear_Mnt','Dokie','Quality_Wind','Cape_Scott']
stn_ids = ['3206','3207','3507','3508']
fcst_hr = ['00','12']
data_columns = [3]
time_step = 3
hub_adjustment = 1.36
to_kmh = 3.6
mod_num = 18



#=========================end of input========================

#contruct timeseries from day1 forecast
start_date = datetime.datetime.strptime(date_range[0], '%d%m%Y')			#convert range to datetime object
end_date = datetime.datetime.strptime(date_range[1], '%d%m%Y')
day_cnt = (end_date-start_date).days										#get number of days in range
rec_cnt = day_cnt*24/time_step												#get number of records available


#import ecmwf data into single array
print('Specified analysis range: ' + date_range[0] + '-' + date_range[1])
print('---------------------------------------------------')
ecmwf_array = np.empty((len(stations),rec_cnt))								#create storage array
for nStn, stn in enumerate(stations):										#loop through stations
	timeseries = []
	print('Creating timeseries for station ' + stn)
	for nDay in (start_date + datetime.timedelta(n) for n in range(day_cnt)):		#loop through all days and runs
		for nRun in fcst_hr:
			filename = raw_dir+stn+'/'+str(nDay.year)+'/'+str(nDay.month)+'/'+nDay.strftime('%Y-%m-%d')+'_'+nRun+'00_'+stn+'.csv'
			if os.path.isfile(filename):									#check if file exists
				raw_data = np.genfromtxt(filename, usecols=data_columns, skip_header=1, autostrip=True,  delimiter=',',dtype=float)
				timeseries.extend(raw_data[0:4])							#append first day data to timeseries
				missing_filler = raw_data[4:8]								#store second day data, in case next file is missing
			else:
				timeseries.extend(missing_filler)							#if missing, fill using previous day's forecast
				print('Filling missing data with previous forecast for ' + filename)
	# ecmwf_array[nStn,:] = timeseries 
	ecmwf_array[nStn,:] = [i * hub_adjustment * to_kmh for i in timeseries ]
print('Importing ECMWF data: complete')

#import obs data into single array
print('---------------------------------------------------')
obs_array = np.empty((len(stations),rec_cnt))								#create storage array
for nStn, stn in enumerate(stn_ids):										#loop through stations
	timeseries = []
	print('Creating timeseries for station ' + stations[nStn])
	for nDay in (start_date + datetime.timedelta(n) for n in range(day_cnt+1)):		#loop through all days and runs
		filename = verif_dir + 'windobs/'+nDay.strftime('%Y%m%d')+'_'+stn+'_SFCWSPD.txt'
		if os.path.isfile(filename) and not (nDay.month==3 and (nDay.day==8 or nDay.day==9 or nDay.day==10)):
			raw_data = np.genfromtxt(filename, usecols=0, skip_header=0, autostrip=True,dtype=float)
			raw_data[raw_data==-999.] = np.nan
			timeseries.extend(raw_data)							#append first day data to timeseries
			if len(raw_data)!= 24:
				missing_filler = np.empty(24)*np.nan
				timeseries.extend(missing_filler)
				print('Data missing for: %s, filling with NaNs' %nDay.strftime('%Y%m%d'))
		else:
			missing_filler = np.empty(24)*np.nan
			timeseries.extend(missing_filler)
			print('Data missing for: %s, filling with NaNs' %nDay.strftime('%Y%m%d'))
	obs_array[nStn,:] = timeseries[4:-20:time_step] 
print('Importing observation data: complete')


#import UBC-SREF data into single array
print('---------------------------------------------------')
ubc_array = np.empty((len(stations),mod_num,rec_cnt))								#create storage array
for nStn, stn in enumerate(stn_ids):										#loop through stations
	timeseries = []
	print('Importing forecast data for ' + stations[nStn])
	for nDay in (start_date + datetime.timedelta(n) for n in range(day_cnt+1)):		#loop through all days and runs
		filename = verif_dir + 'windfcst/'+nDay.strftime('%Y%m%d')+'_'+stn+'_SFCWSPDday1.txt'
		if os.path.isfile(filename):
			raw_data = np.genfromtxt(filename, skip_header=0,autostrip=True,dtype=float)
			raw_data[raw_data==-999.] = np.nan
			timeseries.extend(raw_data)							#append first day data to timeseries
		else:
			print('Data missing for: %s, filling with NaNs' %nDay.strftime('%Y%m%d'))
	timeseries = np.asarray(timeseries).T
	ubc_array[nStn,:,:]	= timeseries[:,4:-20:time_step]
# ubc_array = np.delete(ubc_array,2,1)
ubc_mean_array = np.nanmean(ubc_array, 1)
print('Importing UBC-SREF data: complete')


#calculate correction factor
ecmwf_array_corrected = np.zeros(np.shape(ecmwf_array)) * np.nan
correct_factor = np.nanmean(obs_array,1)/np.nanmean(ecmwf_array,1)
for nStn in range(len(stations)):
	ecmwf_array_corrected[nStn,:] = ecmwf_array[nStn,:] * correct_factor[nStn]

#calculate sliding correction factor
window_len = 10*8
slide_cnt = rec_cnt/window_len
factor_timeseries = np.empty((len(stations),slide_cnt))
for nWindow in range(slide_cnt):
	target_obs = obs_array[:,nWindow*window_len:(nWindow+1)*window_len]
	target_ecmwf = ecmwf_array[:,nWindow*window_len:(nWindow+1)*window_len]
	factor_timeseries[:,nWindow] = np.nanmean(target_obs,1)/np.nanmean(target_ecmwf,1)





print('---------------------------------------------------')
print('Calculating error stats.......')
ensemble_array = np.empty((len(stations),mod_num+1,rec_cnt))
ensemble_array[:,:-1,:] = ubc_array
ensemble_array[:,-1,:] = ecmwf_array_corrected
ensemble_mean_array = np.nanmean(ensemble_array, 1)
test_set = [ecmwf_array_corrected, ubc_mean_array, ensemble_mean_array]

bias_array = np.empty((len(stations),3))
mae_array = np.empty((len(stations),3))
corr_array = np.empty((len(stations),3))
rmse_array = np.empty((len(stations),3))

for nStn, stn in enumerate(stations):
	for nSet in range(3):
		select_set = test_set[nSet]
		fit_idx = np.isfinite(select_set[nStn,:]) & np.isfinite(obs_array[nStn,:])
		slope, intercept, r_value, p_value, std_err = stats.linregress(select_set[nStn,fit_idx], obs_array[nStn,fit_idx])
		mae_array[nStn,nSet] = np.nanmean(abs(select_set[nStn,:] - obs_array[nStn,:]))
		bias_array[nStn,nSet] = np.nanmean(select_set[nStn,:]) - np.nanmean(obs_array[nStn,:])
		rmse_array[nStn,nSet] = np.nanmean((select_set[nStn,:] - obs_array[nStn,:])**2)**(0.5)
		corr_array[nStn,nSet] = r_value
np.savetxt('Bias.txt', bias_array, fmt='%.2f')
np.savetxt('MAE.txt', mae_array, fmt='%.2f')
np.savetxt('RMSE.txt', rmse_array, fmt='%.2f')
np.savetxt('Corr.txt', corr_array, fmt='%.2f')


print('---------------------------------------------------')
print('Plotting.......')

#plot bias correction factor evolution
plt.figure(0, figsize=(30, 15))
for nStn, stn in enumerate(stations):
	plt.subplot(2,2,nStn+1)
	plt.title(stn, fontweight='bold')
	plt.plot(factor_timeseries[nStn,:])
	plt.ylim([0,3])
	plt.ylabel('Bias factor correction')
	plt.xlabel('Sliding window counter (%s points wide)' %window_len)
plt.suptitle('Temporal evolution of bias factor correction')
plt.savefig('bias_factor_evolution.pdf', format = 'pdf')
plt.close()
print('----------bias_factor_evolution.pdf saved')


#plot timeseries for each station
plt.figure(1, figsize=(30, 15))
for nStn, stn in enumerate(stations):
	plt.subplot(2,2,nStn+1)
	l1, = plt.plot(ecmwf_array[nStn,:], color='b')
	l2, = plt.plot(obs_array[nStn,:], 'r--')
	l3, = plt.plot(ubc_mean_array[nStn,:], 'g:')
	plt.title(stn, fontweight='bold')
	plt.ylim((0,80))
	plt.ylabel('Windspeed (km/h)')
plt.suptitle('Hub-hight adjusted windspeed timeseries: Log Law only')
plt.figlegend((l1,l2,l3), ('ECMWF', 'observations', 'UBC-SREF'), loc = 'center right')
plt.savefig('timeseriesLL.pdf', format = 'pdf')
plt.close()
print('----------timeseriesLL.pdf saved')


#boxplots
plt.figure(1, figsize=(20, 10))
for nStn, stn in enumerate(stations):
	ax = plt.subplot(2,2,nStn+1)
	plt.boxplot([ecmwf_array[nStn,:], obs_array[nStn,:], ubc_mean_array[nStn,:]],1)
	plt.title(stn, fontweight='bold')
	plt.ylim([0,80])
	plt.ylabel('windspeed (km/h)')
	ax.set_xticklabels(['ECMWF', 'Observations', 'UBC-SREF'])
plt.suptitle('Hub-height adjusted windspeed boxplots: Log Law only')
plt.savefig('boxplotsLL.pdf', format = 'pdf')
plt.close()
print('----------boxplotsLL.pdf saved')


#plot timeseries for each station CORRECTED 
plt.figure(1, figsize=(30, 15))
for nStn, stn in enumerate(stations):
	plt.subplot(2,2,nStn+1)
	l1, = plt.plot(ecmwf_array_corrected[nStn,:], color='b')
	l2, = plt.plot(obs_array[nStn,:], 'r--')
	l3, = plt.plot(ubc_mean_array[nStn,:], 'g:')
	plt.title('%s: correction factor = %.2f' %(stn, correct_factor[nStn]), fontweight='bold')
	plt.ylim((0,80))
	plt.ylabel('Windspeed (km/h)')
plt.suptitle('Hub-hight adjusted windspeed timeseries: Log Law + Bias Factor')
plt.figlegend((l1,l2,l3), ('ECMWF', 'observations', 'UBC-SREF'), loc = 'center right')
plt.savefig('timeseriesBF.pdf', format = 'pdf')
plt.close()
print('----------timeseriesBF.pdf saved')

#plot timeseries for each station CORRECTED
plt.figure(1, figsize=(20, 10))
for nStn, stn in enumerate(stations):
	ax = plt.subplot(2,2,nStn+1)
	plt.boxplot([ecmwf_array_corrected[nStn,:], obs_array[nStn,:], ubc_mean_array[nStn,:]],1)
	plt.title(stn, fontweight='bold')
	plt.ylim([0,80])
	plt.ylabel('windspeed (km/h)')
	ax.set_xticklabels(['ECMWF_corrected', 'Observations', 'UBC-SREF'])
plt.suptitle('Hub-height adjusted windspeed boxplots: Log Law + Bias Factor')
plt.savefig('boxplotsBF.pdf', format = 'pdf')
plt.close()
print('----------boxplotsBF.pdf saved')
 


#Scatter plot with trendline
plt.figure(1, figsize=(15, 15))
for nStn, stn in enumerate(stations):
	fit_idx = np.isfinite(ecmwf_array_corrected[nStn,:]) & np.isfinite(obs_array[nStn,:])
	slope, intercept, r_value, p_value, std_err = stats.linregress(ecmwf_array_corrected[nStn,fit_idx], obs_array[nStn,fit_idx])
	ax = plt.subplot(2,2,nStn+1)
	plt.scatter(ecmwf_array_corrected[nStn,:], obs_array[nStn,:], s=2, color='b')
	xvals = np.arange(0,80,0.5)
	plt.plot(xvals, slope*xvals + intercept, 'r-')
	plt.title('%s: R=%.2f, slope=%.2f' %(stn, r_value, slope), fontweight='bold', fontsize=10)
	plt.ylim([0,80])
	plt.xlim([0,80])
	plt.xlabel('forecast windspeed (km/h)')
	plt.ylabel('observed windspeed (km/h)')
	corr_array[nStn,0] = r_value
plt.suptitle('Scatter Plot + Linear Regression')
plt.savefig('scatterBF.pdf', format = 'pdf')
plt.close()
print('----------scatterBF.pdf saved')


#Scatter plot with trendline
plt.figure(1, figsize=(15, 15))
for nStn, stn in enumerate(stations):
	fit_idx = np.isfinite(ubc_mean_array[nStn,:]) & np.isfinite(obs_array[nStn,:])
	slope, intercept, r_value, p_value, std_err = stats.linregress(ubc_mean_array[nStn,fit_idx], obs_array[nStn,fit_idx])
	ax = plt.subplot(2,2,nStn+1)
	plt.scatter(ubc_mean_array[nStn,:], obs_array[nStn,:], s=2, color='b')
	xvals = np.arange(0,80,0.5)
	plt.plot(xvals, slope*xvals + intercept, 'r-')
	plt.title('%s: R=%.2f, slope=%.2f' %(stn, r_value, slope), fontweight='bold', fontsize=10)
	plt.ylim([0,80])
	plt.xlim([0,80])
	plt.xlabel('forecast windspeed (km/h)')
	plt.ylabel('observed windspeed (km/h)')
	corr_array[nStn,1] = r_value
plt.suptitle('Scatter Plot + Linear Regression')
plt.savefig('scatterBF_UBC.pdf', format = 'pdf')
plt.close()
print('----------scatterBF_UBC.pdf saved')



for nStn, stn in enumerate(stations):
	# obs_set = list(obs_array[nStn,:])
	obs_set = obs_array[nStn,:]
	ecmwf_set = ecmwf_array_corrected[nStn,:]
	obs_set_trimmed = obs_set[np.isfinite(obs_set)]
	# obs_set = [value for value in obs_set if not np.isnan(value)]
	ecmwf_set = ecmwf_set[np.isfinite(obs_set)]
	np.savetxt('spectral_obs_%s.csv' %stn, obs_set)
	np.savetxt('spectral_ecmwf_%s.csv' %stn, ecmwf_set)



print('---------------------------------------------------')
print('Formatting and saving data.......')
smpl_rate = 24/time_step
for nStn, stn in enumerate(stn_ids):
	for nDay, day in enumerate((start_date + datetime.timedelta(n) for n in range(day_cnt))):		#loop through all days and runs
		obs_save_data = obs_array[nStn,nDay*smpl_rate:(nDay+1)*smpl_rate]
		fcst_save_data = ubc_array[nStn,:,nDay*smpl_rate:(nDay+1)*smpl_rate]
		fcst_new_col = ecmwf_array_corrected[nStn,nDay*smpl_rate:(nDay+1)*smpl_rate]
		obs_save_data[np.isnan(obs_save_data)] = -999
		fcst_save_data[np.isnan(fcst_save_data)] = -999
		fcst_save_data = np.concatenate((fcst_save_data, np.expand_dims(fcst_new_col, axis=0)))
		filename_obs = comps_data_dir + 'courseObs/data/'+day.strftime('%Y%m%d')+'_'+str(stn)+'_SFCWSPD.txt'
		filename_fcst = comps_data_dir + 'courseFcst/data/'+day.strftime('%Y%m%d')+'_'+str(stn)+'_SFCWSPD.txt'
		np.savetxt(filename_obs, obs_save_data, fmt='%.2f')
		np.savetxt(filename_fcst, fcst_save_data.T, fmt='%.2f')




