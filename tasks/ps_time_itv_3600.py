from logging import log
import logging
import os
import sys
import datetime

directory = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(directory, '..'))
from config import get_config
from common.sendmail import send_mail
from common.distribute import distribute

log_level = get_config().get("log_level")
inventory = get_config().get("ansible_inventory")
process_timeout = get_config().get("process_timeout")

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=log_level)

    cmd = 'ps -ef | grep plots | grep -v grep | awk \'{if($7>"' + \
        process_timeout+'}")print $2}\''

    d = distribute(inventory=inventory, connection='smart')

    logging.info('hosts=\'all\', module="shell", args='+cmd)
    d.run(hosts='all', module="shell", args=cmd)
    r = d.get_result()
    if r['success']:
        for key in r['success'].keys():
            if r['success'][key]['stdout']:
                logging.warning('Host {0} has plots processes with execution times longer than {1}, pid: {2}'.format(
                    key,
                    process_timeout,
                    r['success'][key]['stdout'].replace('\n', '/')
                ))

                send_mail('WARNING: Process timeout', '''
Current Time: {0}
warning: Host {1} has plots processes with execution times longer than {2}
pid: 
{3}
                '''.format(
                    datetime.datetime.now(),
                    key,
                    process_timeout,
                    r['success'][key]['stdout']
                ))
    else:
        for key in r['failed'].keys():
            logging.error(r['failed'][key]['msg'])
