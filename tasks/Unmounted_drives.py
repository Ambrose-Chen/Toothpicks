#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import json


def Unmounted_drives(d_json):
    um = []
    for i in d_json:
        if 'children' in i.keys():
            um.extend(Unmounted_drives(i['children']))
        else:
            if not i["mountpoint"] and 'T' in i["size"]:
                um.append(i["name"])
    return um


if __name__ == '__main__':

    disk_condition = os.popen('lsblk -J').read()
    d_json = json.loads(disk_condition)
    um = Unmounted_drives(d_json["blockdevices"])
    if um:
        print(Unmounted_drives(d_json["blockdevices"]))
