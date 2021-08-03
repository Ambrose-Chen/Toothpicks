import telnetlib
import threading
import queue
import logging
import datetime

import sys
import os
directory = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(directory, '..'))
from config import get_config
from common.sendmail import send_mail


hosts = get_config().get("scan_hosts")
ports = get_config().get("scan_ports")


def get_ip_status(ip, ports):
    server = telnetlib.Telnet()
    for port in ports:
        try:
            server.open(ip, port)
            logging.info('{0} port {1} is open'.format(ip, port))
        except Exception as err:
            logging.error('{0} port {1} is not open'.format(ip, port))

            send_mail('ERROR: {0} port {1} is not open'.format(ip, port), '''
Current Time: {0}
Host: {1}
Port: {2}
Error: Port is not listening
            '''.format(
                datetime.datetime.now(),
                ip,
                port))

        finally:
            server.close()


def check_open(q):
    try:
        while True:
            ip = q.get_nowait()
            get_ip_status(ip, ports)
    except queue.Empty as e:
        pass


if __name__ == '__main__':
    threads = []
    q = queue.Queue()

    logging.basicConfig(
        format='%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level='INFO')

    for ip in hosts:
        q.put(ip)
    threads = []
    for i in range(10):
        t = threading.Thread(target=check_open, args=(q,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
