
#!/bin/bash
#===================
# run_getECMWF.bash
#===================

#bash script for running getECMWF.py (to be ran from crontab)
echo ------------- ECMWF automatic data fetch ----------------

CURRENT_TIME=$(date +%d-%m-%Y_%H:%M:%S)						#get current timestamp

mkdir -p ./ECMWFlogs										#create logs directory, if doesn't exist

echo ...running getECMWF.py to download and convert data.
python2.7 ./getECMWF.py >& "./ECMWFlogs/$CURRENT_TIME.txt"	#run python script, save output

echo ...removing downloaded xml files
rm ./run/*													#remove all script files

> WND_HUB.1.t.OK

echo ECMWF download attempt complete: $date
echo Check status log in ./ECMWFlogs directory
echo ---------------------------------------------------------