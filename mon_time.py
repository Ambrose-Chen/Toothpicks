import os
import re
import argparse
import threading
from common import process
dir = os.path.split(os.path.realpath(__file__))[0]
tasks_dir = os.path.join(dir, 'tasks')
from config import get_config

python_env = get_config().get("python_env")




def _runtime_timer(interval, mathod, task):
    script_env = {
        'sh': 'bash',
        'py': python_env
    }
    if task['suffix'] in script_env.keys():
        process.async_sub_process('{0} {1}'.format(
            script_env[task['suffix']],
            os.path.join(tasks_dir, task['script'])
        ))

    global _time
    _time = threading.Timer(interval, mathod, (interval, mathod, task))
    _time.start()


if __name__ == '__main__':
    tasks_dic = {}

    parser = argparse.ArgumentParser()

    parser.add_argument('-a', '--all', type=int, default=0,
                        const=1, nargs='?', help='Perform all tasks')

    for task in os.listdir(tasks_dir):
        task_re = re.search('^(.*)_itv_([0-9]+)\.([sp][hy])$', task)
        if not os.path.isdir(task) and task_re:
            tasks_dic[task_re.group(1)] = {
                'script': task_re.group(0),
                'interval': int(task_re.group(2)),
                'suffix': task_re.group(3)
            }

            parser.add_argument('--' + task_re.group(1), type=int,
                                default=0, const=task_re.group(2), nargs='?')

    arg = parser.parse_args()
    _args = arg.__dict__.copy()
    _args.pop('all')
    for key, val in _args.items():
        if arg.all:
            p = threading.Timer(tasks_dic[key]['interval'], _runtime_timer,
                                (tasks_dic[key]['interval'], _runtime_timer, tasks_dic[key]))
            p.start()
        elif val:
            p = threading.Timer(val, _runtime_timer,
                                (val, _runtime_timer, tasks_dic[key]))
            p.start()
