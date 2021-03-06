
#!/bin/bash
#===================
# run_getECMWF.bash
#===================

#bash script for running getECMWF.py (to be ran from crontab)
echo ------------- ECMWF automatic data fetch ----------------

CURRENT_TIME=$(date +%d-%m-%Y_%H:%M:%S)						#get current timestamp

mkdir -p /Users/nadya2/code/ECMWFlogs						#create logs directory, if doesn't exist

echo ...running getECMWF.py to download and convert data.
python /Users/nadya2/code/getECMWF.py >& "/Users/nadya2/code/ECMWFlogs/$CURRENT_TIME.txt"	#run python script, save output

echo ...removing downloaded xml files
rm *xml														#remove xml files

echo ECMWF download attempt complete: $date
echo Check status log in /Users/nadya2/code/ECMWFlogs directory
echo ---------------------------------------------------------