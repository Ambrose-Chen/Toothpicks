import os
import json

def get_blk_json():
    pro = os.popen("lsblk -J")
    output = pro.read()
    pro.close()
    return output

def unmounted(blk):
    unmounted_blk = []
    if 'children' in blk.keys():
        for c in blk["children"]:
            unmounted(c)
    else:
        if blk["mountpoint"] == None and "T" in blk["size"]:
            unmounted_blk.append(blk)

    return unmounted_blk


def get_unmounted_blk():
    blk_json = get_blk_json()
    blk_dict = json.loads(s=blk_json)
    unmounted_blk = []
    for i in blk_dict["blockdevices"]:
        u_blk = unmounted(i)
        if u_blk:
            unmounted_blk.append(unmounted(i))

    return unmounted_blk
