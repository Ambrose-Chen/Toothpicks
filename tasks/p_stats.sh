#!/bin/bash


result=`ansible all -m shell -a '/usr/local/bin/chia-blockchain/venv/bin/chia farm summary | grep -E "Plot count|Total size of plots"'`

result=`echo "$result" | sed -e 's/|\ CHANGED.*//g'`

total_plot_count=`echo "$result" | grep "Plot count" | awk -F':' 'BEGIN{SUM=0}{SUM+=$2}END{print SUM}'`
total_size_of_plots=`echo "$result" | grep "Total size of plots" | awk 'BEGIN{SUM=0}{if($6=="TiB"){SUM+=$5}else if($6=="GiB"){SUM+=$5/1024}}END{print SUM}'`


echo -e "$result \n"
echo -e "total plot count: $total_plot_count"
echo -e "total size of plots: $total_size_of_plots TiB"
