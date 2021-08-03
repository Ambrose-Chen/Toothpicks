#!/bin/bash




plots_proc=`ps -ef| grep -v grep | grep plot | awk '{print $2}'`

for i in $plots_proc
do
	strace -p $i &> /tmp/strace_tmp &
	sleep 2
	kill -SIGINT $!
	cat /tmp/strace_tmp | grep -v '^strace:' | grep -v '<detached ...>' &>/dev/null
	if [ $? -ne 0 ]; then
		echo "$i"
	fi
done
