import subprocess


def async_sub_process(command):
    subprocess.Popen(command, shell=True)
