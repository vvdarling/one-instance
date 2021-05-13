from os import path
from subprocess import check_output
from globals import *

NETPFX = "10.208.129"
set_pfx(NETPFX)
NETMASK = "255.255.255.0"
GATEWAY = IP(254)


SERVER_PHYS_CORES = 11
SERVER_L2 = 256 * 1024
SERVER_L3 = 30 * 1024 * 1024

CLIENT_NAME_201 = "server129-2"
CLIENT_SET = [CLIENT_NAME_201]

MACHINES = {}
MACHINES["server129-1"] = {
    'nics': {
        'enp26s0f1': {
            'driver': 'spdk',
            'pci': '0000:1a:00.1',
            'mac': 'e0:4f:43:de:17:a1',
            'ip': IP(22),
        }
    },
    'oob_ip': '10.208.129.1',
    'node0_cores': range(2, 14, 2),
    'numa_nodes': 4,
}
MACHINES["server129-2"] = {
    'nics':{
        'enp26s0f1' : {
            'driver': 'spdk',
            'mac': 'e0:4f:43:de:17:9d',
            'ip' : '10.208.129.2'
        }
    },
    'oob_ip': '10.208.129.2',
    'node0_cores': range(2, 14, 2),
}
# MACHINES["client1"] = {
#     'nics':{
#         'enp26s0f1' : {
#             'driver': 'spdk',
#             'mac': 'e0:4f:43:de:17:9d',
#             'ip' : '10.208.129.2'
#         }
#     },
#     'oob_ip': '10.208.129.2',
#     'node0_cores': range(8)
# }

# MACHINES[CLIENT_NAME_201] = {
#     'nics':{
#         'enp0s17:' : {
#             'driver': 'spdk',
#             'mac': '08:00:27:17:ee:46',
#             'ip' : '10.208.129.201'
#         }
#     },
#     'oob_ip': '10.208.129.201',
#     'node0_cores': range(2, 20, 2)
# }

THISHOST = check_output("hostname -s", shell=True).strip().decode('utf-8')
SCRIPT_DIR = path.split(path.realpath(__file__))[0]

from base_dir import BASE_DIR
SDIR = "{}/caladan".format(BASE_DIR)
ZDIR = "{}/zygos-bench/".format(BASE_DIR)
CLIENT_BIN = "{}/apps/synthetic/target/release/synthetic".format(SDIR)
OBSERVER = None
RSTAT = SDIR + "/scripts/rstat.go"
STORAGE_HOST = "zig"

binaries = {
    'iokerneld': {
        'ht': "{}/iokerneld".format(SDIR),
    },
    'memcached': {
        'linux': "{}/memcached-linux/memcached".format(BASE_DIR),
        'shenango': "{}/memcached/memcached".format(BASE_DIR),
    },
    'swaptions': {
        'linux': "{}/parsec/pkgs/apps/swaptions/inst/amd64-linux.gcc-pthreads/bin/swaptions".format(BASE_DIR),
        'shenango': "{}/parsec/pkgs/apps/swaptions/inst/amd64-linux.gcc-shenango/bin/swaptions".format(BASE_DIR),
        'linux-floating': "{}/parsec/pkgs/apps/swaptions/inst/amd64-linux.gcc-pthreads/bin/swaptions".format(BASE_DIR),
    },
    'streamcluster': {
        'linux': "{}/parsec/pkgs/kernels/streamcluster/inst/amd64-linux.gcc-pthreads/bin/streamcluster".format(BASE_DIR),
        'shenango': "{}/parsec/pkgs/kernels/streamcluster/inst/amd64-linux.gcc-shenango/bin/streamcluster".format(BASE_DIR),
        'linux-floating': "{}/parsec/pkgs/kernels/streamcluster/inst/amd64-linux.gcc-pthreads/bin/streamcluster".format(BASE_DIR),
    },
    'x264': {
        'linux': '{}/parsec/pkgs/apps/x264/inst/amd64-linux.gcc-pthreads/bin/x264'.format(BASE_DIR),
        'shenango': "{}/parsec/pkgs/apps/x264/inst/amd64-linux.gcc-shenango/bin/x264".format(BASE_DIR),
        'linux-floating': '{}/parsec/pkgs/apps/x264/inst/amd64-linux.gcc-pthreads/bin/x264'.format(BASE_DIR),
    },
    'stress_shm': {
        'shenango': "{}/apps/netbench/stress_shm".format(SDIR),
        'linux': "{}/apps/netbench/stress_linux".format(SDIR),
    },
    'silo': {
        'shenango': '{}/silo/silotpcc-shenango'.format(BASE_DIR),
        'linux': '{}/silo.linux/silotpcc-linux'.format(BASE_DIR),
    },
    'stress_shm_query': {
        'linux': "{}/apps/netbench/stress_shm_query".format(SDIR),
    },
    'synthetic': {
        'shenango': "{}/apps/synthetic/target/release/synthetic --config".format(SDIR),
    }
}

def thishost_cores():
    return MACHINES[THISHOST]['node0_cores']

def thishost_shen_cores():
    cores = thishost_cores()
    return cores[1:len(cores)/2] + cores[len(cores)/2+1:]

def max_cores():
    return len(thishost_cores()) - 2

def control_core():
    return 0

def get_nic(host):
    return list(MACHINES[host]['nics'].values())[0]

def get_nic_name(host):
    return list(MACHINES[host]['nics'].keys())[0]

def get_linux_ip(host):
    return list(MACHINES[host]['nics'].values())[0]['ip']


def gen_conf(filename, experiment, mac=None, **kwargs):
    conf = [
        "host_addr {ip}",
        "host_netmask {netmask}",
        "host_gateway {gw}",
        "runtime_kthreads {threads}",
        "runtime_guaranteed_kthreads {guaranteed}",
        "runtime_spinning_kthreads {spin}"
    ]
    if mac:
        conf.append("host_mac {mac}")

    conf += kwargs.get('custom_conf', [])

    # HACK
    if kwargs['guaranteed'] > 0:
        if not kwargs.get('enable_watchdog', False):
            conf.append("disable_watchdog true")
        conf.append("runtime_priority lc")
    else:
        conf.append("runtime_priority be")

    # if experiment['system'] == "shenango":
    for host in experiment['hosts']:
        for i, cfg in enumerate(experiment['hosts'][host]['apps']):
            if cfg['ip'] == kwargs['ip']:
                continue
            if "shenango" != cfg.get('system', experiment['system']):
                if i == 0:
                    m = list(MACHINES[cfg['host']]['nics'].values())[0]['mac']
                    conf.append("static_arp {ip} {mac}".format(
                        mac=m, ip=cfg['ip']))
            else:
                conf.append("static_arp {ip} {mac}".format(**cfg))

    if experiment.get('observer'):
       obs = experiment['observer']
       observer_nic = list(MACHINES[obs]['nics'].keys())[0]
       observer_mac = MACHINES[obs]['nics'][observer_nic]['mac']
       conf.append("static_arp {} {}".format(OBSERVER_IP, observer_mac))

    with open(filename, "w") as f:
        f.write("\n".join(conf).format(
            netmask=NETMASK, gw=GATEWAY, mac=mac, **kwargs) + "\n")
