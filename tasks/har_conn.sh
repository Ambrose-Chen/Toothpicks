#!/bin/bash

while [ 1 ]
do
	sleep 1
	lsof -i:8447 | grep ESTABLISHED | grep -v '>localhost:36180' | sed "s/localhost/`ip a | grep -A4 eno1| grep 'inet '| awk '{print $2}' | awk -F'/' '{print $1}' | sed 's/\./-/g'`.xxx/g" | awk -F'>' '{print $2}' | awk -F'.' '{print $1}'| sed 's/-/./g'| sort -u > /tmp/_listen_8447
	cat /etc/ansible/hosts |grep -v '\#'| grep chia | awk '{print $2}' | awk -F'=' '{print $2}'| sort -u > /tmp/_ansible_host
	diff /tmp/_listen_8447 /tmp/_ansible_host |grep '> ' | grep -v '^$'| awk '{print $2}' > /tmp/har_conn
done
