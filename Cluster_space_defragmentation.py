import os
import json
import time
import random
import argparse
from random import shuffle
from common import distribute
from multiprocessing import Pool

def get_cluster_space_left(hosts):
    space_left_com = 'df | sed -n \'1!p\' | awk \'{if($2>1000000000){print $0}}\' | awk \'{print $4,$6}\''

    adhoc = distribute.distribute(connection='smart', inventory='/etc/ansible/hosts')
    adhoc.run(hosts=hosts, module='shell', args=space_left_com)

    space_left_ansible = adhoc.get_result()

    space_left = {}

    for key, val in space_left_ansible["success"].items():
        space_left[key] = {}
        for i in val["stdout_lines"]:
            space_left[key][i.split()[1]] = int(i.split()[0])

    if space_left_ansible["failed"]:
        print(space_left_ansible["failed"])
    if space_left_ansible["unreachable"]:
        print(space_left_ansible["unreachable"])
    return space_left

def get_all_plots_in_the_mount_dir(hosts):
    all_plots_com = 'find `df | sed -n \'1!p\' | awk \'{if($2>1000000000){print $0}}\' | awk \'{print $6}\'` -type f -name *plot -exec ls -l --block-size K {} \;'

    adhoc = distribute.distribute(connection='smart', become=True, become_user='root', become_method='sudo', inventory='/etc/ansible/hosts')
    adhoc.run(hosts=hosts, module='shell', args=all_plots_com)

    all_plots_ansible = adhoc.get_result()

    all_plots = {}

    for key, val in all_plots_ansible["success"].items():
        all_plots[key] = {}
        for i in val["stdout_lines"]:
            det_plot = i.split()
            all_plots[key][det_plot[len(det_plot) - 1]] = {
                    'mod': det_plot[0],
                    'user': det_plot[2],
                    'group': det_plot[3],
                    'size': int(det_plot[4].replace('K', ''))
                    }
    if all_plots_ansible["failed"]:
        print(all_plots_ansible["failed"])
    if all_plots_ansible["unreachable"]:
        print(all_plots_ansible["unreachable"])
    return all_plots


def find_undersized_plots(all_plots):
    result = {}
    for key, val in all_plots.items():
        for k, v in val.items():
            if v["size"] < 108000000000:
                if key not in result.keys():
                    result[key] = []

                result[key].append(k)

    return result

def rite_json_file(_dict, _file):
    with open(_file, 'w') as wf:
        json.dump(_dict, wf, indent=4, sort_keys=True)

def statistical_analysis(space, plots):
    all_space = 0 
    for H, ss in space.items():
        h_space = 0
        for m, s in ss.items():
            h_space += s

        print(H + ": " + str(h_space))
        all_space += h_space

    print('total size of space left: ' + str(all_space))

    all_plots_s = 0
    for h, ps in plots.items():
        h_plots_s = 0
        for p, v in ps.items():
            h_plots_s += v['size']
        print(h + ": " + str(h_plots_s))
        all_plots_s += h_plots_s

    print('total size of plots: ' + str(all_plots_s))



def get_space_s_m(space):
    for H, ss in space.items():
        for m, s in ss.items():
            print(H + m + " " + str(s))
            yield {
                    'host': H,
                    'mount': m,
                    'size': s
                    }

def cluster_rsync(input_file, output_file, playbook_file):
    _tmp_playbook = '''
- hosts: dest_host
  gather_facts: no
  tasks:
    - synchronize:
        src: src_file
        dest: dest_file
      delegate_to: src_host
    '''
    src_host = input_file.split(':')[0]
    src_file = input_file.split(':')[1]
    dest_host = output_file.split(':')[0]
    dest_file = output_file.split(':')[1]
    with open(playbook_file, 'w') as wf:
        wf.writelines(_tmp_playbook.replace('src_host', src_host).replace('src_file', src_file).replace('dest_host', dest_host).replace('dest_file', dest_file))
    
    pb = distribute.distribute(connection='smart', inventory='/etc/ansible/hosts')
    pb.playbook(playbooks=[playbook_file])
    rsync_ansible = pb.get_result()
    if rsync_ansible["failed"]:
        print(rsync_ansible["failed"])
    if rsync_ansible["unreachable"]:
        print(rsync_ansible["unreachable"])

    os.remove(playbook_file)

    

#def get_space_r(space):
def balanceing_resources():
    pass
    
def balance_migration(space, plots, emp_host):
    m_plots = {}
    m_plots_d = {}
    match = []
    pop_space = {}
    for i in emp_host:
        pop_space[i] = space.pop(i)
        m_plots[i] = plots[i]

    # Calculate all remaining space
    all_space = 0
    for H, ss in space.items():
        for m, s in ss.items():
            all_space += s
            

    # Size of all plots
    all_plots_s = 0

    # Number of all plots
    num_plots = 0

    # Calculate the number of plots per disk
    pl = {}
    for h, ps in m_plots.items():
        pl[h] = {}
        m_plots_d[h] = {}
        for p, v in ps.items():
            for i in pop_space[h].keys():
                if i + '/' in p:
                    dirc = i
                    break
            if dirc in pl[h].keys():
                m_plots_d[h][dirc][p] = v
            else:
                m_plots_d[h][dirc] = {p: v}

            if dirc in pl[h].keys():
                pl[h][dirc] += 1
            else:
                pl[h][dirc] = 1

            all_plots_s += v['size']
            num_plots += 1
    
    print(pl)
    # Number of drives to be migrated
    blk_num = 0
    for h, s in pop_space.items():
        blk_num += len(s.keys())

    if all_space > all_plots_s:
        num_re_p = 0
        print('Average remaining space after migration of %d disks is 0, about %d' % (blk_num, num_re_p))
    else:
        # Average number of remaining plots per disk
        #
        #   all_plots_s - all_space:    Size of remaining plots
        #   blk_num:                    Number of drives to be migrated
        #   all_plots_s/num_plots:      Average size of plots
        num_re_p = int((all_plots_s - all_space)/blk_num/(all_plots_s/num_plots))
        print('Average remaining space after migration of %d disks is %d, about %d' % (blk_num, (all_plots_s - all_space)/blk_num, num_re_p))



    print(m_plots_d)
    print(space)
    
    _ss = get_space_s_m(space)

    sp = next(_ss)
    try:
        for h, ds in m_plots_d.items():
            for d, ps in ds.items():
                i = pl[h][d]
                for p in ps.keys():
                    if i <= num_re_p:
                        break

                    while sp['size'] < ps[p]['size'] + 1:
                        sp = next(_ss)

                    sp['size'] -= (ps[p]['size'] + 1)
                    print('plots:'+h+':'+p+'---'+sp['host']+':'+sp['mount'])

                    pl[h][d] -= 1
                    i -= 1
    except StopIteration as e:
        pass

    print(pl)


def sequential_migration(space, plots, emp_host):
    m_plots = {}
    match = []
    for i in emp_host:
        space.pop(i)
        m_plots[i] = plots[i]

    print(space)
    _ss = get_space_s_m(space)
    try:
        sp = next(_ss)
        for h, ps in m_plots.items():
            for p, v in ps.items():
                while sp['size'] < v['size'] + 1:
                    sp = next(_ss)
                    
                sp['size'] -= (v['size'] + 1)
                print('plots:'+h+':'+p+'---'+sp['host']+':'+sp['mount'])
    except StopIteration as e:
        while True:
            print('\033[31mThere is not enough space left in the cluster to release resources. Enter `y` to Continue migration(y/n): \033[0m', end='')
            _a = input()
            if _a == 'y' or _a == 'n':
                break

    
    #print(m_plots, space)

def process_pool(processes, tasks):
    po = Pool(processes)

    for 
    po.apply_async(cluster_rsync, ())



    
def mkdir(*args):
    for _dir in args:
        if not os.path.isdir(_dir):
            os.mkdir(_dir)

if __name__ == '__main__':

    tmp_dir = os.environ['HOME'] + '/.Cluster_space_defragmentation'
    pb_dir = tmp_dir + '/playbook'
    plots_file = tmp_dir + '/plots'
    space_file = tmp_dir + '/space'

    mkdir(tmp_dir, pb_dir) 

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--action', choices=['release', 'balance', 'rel-bal'], type=str, help='')
    #parser.add_argument('-A', '--Algorithm', choices=['ord', 'rand'], type=str, help='')
    parser.add_argument('-H', '--hosts', type=str, help='')
    parser.add_argument('-l', '--list', type=int, default=0, const=1, nargs='?')
    parser.add_argument('-u', '--update', type=str, help='')
    parser.add_argument('-p', '--pool', type=int, default=8)

    arg = parser.parse_args()
    if arg.update:
        space_left = get_cluster_space_left(arg.update)
        all_plots = get_all_plots_in_the_mount_dir(arg.update)
        write_json_file(all_plots, plots_file)
        write_json_file(space_left, space_file)

    if (arg.action and arg.hosts) or arg.list:
        with open(space_file, 'r') as f: 
            space = json.load(f)
        with open(plots_file, 'r') as f:
            plots = json.load(f)

    if arg.list:
        statistical_analysis(space, plots)

    if arg.action == 'release' and arg.hosts:
        sequential_migration(space, plots, arg.hosts.split(','))
    elif arg.action == 'rel-bal' and arg.hosts:
        balance_migration(space, plots, arg.hosts.split(','))

    #cluster_rsync('chia-170-10-0-11:/tmp/a', 'chia-170-10-0-12:/tmp/a', pb_dir + '/' + time.strftime('%Y%m%d%H%M%S',time.localtime(time.time())))
