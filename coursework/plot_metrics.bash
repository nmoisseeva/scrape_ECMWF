#bash plotting script for Comps

current_dir=$(pwd)
lcns=(0 1 2 3)
tags=(BearMountain Dokie QualityWind CapeScott)
metrics=(crps mae bias corr crmse)
metrics2=(reliability pithist)
metrics3=(droc taylor)

cd /Users/nadya2/Applications/Comps-master/
# ./comps.exe 20150130 20150420 nadya

for m in "${metrics[@]}"
	do
	for i in "${lcns[@]}"
		do
		cd /Users/nadya2/Applications/Comps-master/results/nadya/verif
		plt_title=${tags[$i]}
		img_file=${current_dir}/${m}_$plt_title.pdf
		/Users/nadya2/Applications/Comps-master/graphics2/verif Wind_nadyaECMWF_0.nc Wind_nadyaUBC_0.nc Wind_raw_0.nc -m $m -r 20 -l $i -tickfs 10 -labfs 10 -legfs 10 -title $plt_title -xlabel "Forecast Hour (h)" -leg ECMWF,UBS-SREF,Ensemble -f $img_file 
		echo "Location $plt_title saved in $img_file"
	done
done


for n in "${metrics2[@]}"
	do
	for j in "${lcns[@]}"
			do
			cd /Users/nadya2/Applications/Comps-master/results/nadya/verif
			plt_title=${tags[$j]}
			img_file=${current_dir}/${n}_$plt_title.pdf
			/Users/nadya2/Applications/Comps-master/graphics2/verif Wind_nadyaUBC_0.nc Wind_raw_0.nc -m $n -r 20 -l $j -tickfs 10 -labfs 10 -legfs 10  -leg UBS-SREF,Ensemble -f $img_file 
			echo "Location $plt_title saved in $img_file"
	done
done


for l in "${metrics3[@]}"
	do
	for k in "${lcns[@]}"
		do
		cd /Users/nadya2/Applications/Comps-master/results/nadya/verif
		plt_title=${tags[$k]}
		img_file=${current_dir}/${l}_$plt_title.pdf
		/Users/nadya2/Applications/Comps-master/graphics2/verif Wind_nadyaECMWF_0.nc Wind_nadyaUBC_0.nc Wind_raw_0.nc -m $l -r 20 -l $k -tickfs 10 -labfs 10 -legfs 10 -title $plt_title -leg ECMWF,UBS-SREF,Ensemble -f $img_file 
		echo "Location $plt_title saved in $img_file"
	done
done