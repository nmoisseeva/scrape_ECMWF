
#!/bin/bash
#===================
# run_getECMWF.bash
#===================

#bash script for running getECMWF.py (to be ran from crontab)
echo ------------- ECMWF automatic data fetch ----------------

CURRENT_TIME=$(date +%d-%m-%Y_%H:%M:%S)						#get current timestamp

mkdir -p ./ECMWFlogs										#create logs directory, if doesn't exist

echo ...running getECMWF.py to download and convert data.
python /Users/nmoisseeva/code/getECMWF.py >& "/Users/nmoisseeva/code/ECMWFlogs/$CURRENT_TIME.txt"	#run python script, save output

echo ...removing downloaded xml files
rm *xml														#remove xml files

echo ECMWF download attempt complete: $date
echo Check status log in /Users/nmoisseeva/code/ECMWFlogs directory
echo ---------------------------------------------------------