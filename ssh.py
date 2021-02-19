from pssh.agent import SSHAgent
from pssh.utils import load_private_key
from pssh.clients.native.parallel import ParallelSSHClient
from gevent import joinall
from pssh.utils import enable_host_logger
import os
import json
enable_host_logger()

def pip_install(hosts):
    run(hosts, "apt install --yes python3-pip")
    run(hosts, "pip3 install pillow numpy")

def docker_install(hosts):
    run(hosts, "apt-get update")
    run(hosts, "apt-get install --yes apt-transport-https ca-certificates curl gnupg-agent software-properties-common")
    run(hosts, "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -")
    run(hosts, "add-apt-repository \"deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable\" ")
    run(hosts, "apt-get update")
    run(hosts, "apt-get install --yes docker-ce docker-ce-cli containerd.io")
    run(hosts, "pip3 install docker-compose")

def prepare_mount(hosts):
    hosts = filter_for_mount(hosts)
    run(hosts, "mkdir mount")
    run(hosts, "apt install --yes nfs-common")
    run(hosts, "mount -t nfs blrsharenfs.corp.adobe.com:ifs/data/fl_architecture /root/mount")

def filter_by_dir(hosts, dir):
    client = ParallelSSHClient(hosts)
    o = client.run_command("ls")
    filtered = []
    for host in hosts:
        if dir not in o[host].stdout:
            filtered.append(host)
    return filtered

def filter_for_mount(hosts):
    client = ParallelSSHClient(hosts)
    o = client.run_command("df -T")
    filtered = []
    for host in hosts:
        for l in o[host].stdout:
            if 'nfs' in l.split():
                filtered.append(host)
    return list(set(hosts) - set(filtered))

def run(hosts, command):
    client = ParallelSSHClient(hosts)
    output = client.run_command(command)
    client.join(output, consume_output=True)
    """for host, host_output in output.items():
        print(host, " : ")
        for line in host_output.stdout:
            print(line)
        for line in host_output.stderr:
            print(line)"""

def mount(hosts):
    unmounted = filter_for_mount(hosts)
    run(unmounted, "mount -t nfs blrsharenfs.corp.adobe.com:ifs/data/fl_architecture /root/mount")

def new_project(hosts):
    for host in hosts:
        os.system("rsync -av --exclude='.git/' --exclude='data/' --exclude='models/' --exclude='updates/' -e 'ssh -o StrictHostKeyChecking=no' --delete /root/FL_Architecture root@" + host + ":/root/")

def project_sync(hosts):
    for host in hosts:
        os.system("rsync -av --exclude='.git/' --exclude='data/' --exclude='models/' --exclude='updates/' -e 'ssh -o StrictHostKeyChecking=no' --delete /root/FL_Architecture/ root@" + host + ":/root/FL_Architecture")

def leave_swarm(hosts):
    run(hosts, "docker swarm leave --force")

def join_swarm(hosts, token_command = "docker swarm join --token SWMTKN-1-26g7vqj85zghcqqjjh6ayp6b95s0n5v8xhteov0qi016cm1g54-0h5luhibx7klod7j3jkvhfy6b 10.42.67.192:2377"):
    run(hosts, token_command)

def setips(hosts):
    with open("/etc/docker/daemon.json") as f:
        daemon = json.load(f)
    i = 1
    for host in hosts:
        host_split = host.split('.')[-2:]
        ip = "172." + str(i) + "." + host_split[0] + "." + "0/16"
        i += 1 
        print(ip)
        daemon["default-address-pools"][0]["base"] = ip
        with open("/root/daemon/" + host + ".json", 'w') as f:
            json.dump(daemon, f)
    for host in hosts:
        os.system("rsync -av -e 'ssh -o StrictHostKeyChecking=no' --delete /root/daemon/" + host + ".json root@" + host + ":/etc/docker/daemon.json")

def datasampling(hosts):
    run(hosts, "cd FL_Architecture; python3 scripts/datasampling.py cifar-10 60")

def sync_and_clear(hosts):
    project_sync(hosts)
    run(hosts, "docker rm --force $(docker ps -aq)")

hosts = ["10.42.67.177", "10.42.72.138",
        "10.42.64.171", "10.42.64.187", "10.42.67.110", "10.42.66.154", "10.42.64.160", 
        "10.42.70.2", "10.42.64.167", "10.42.67.123", "10.42.70.13", "10.42.64.175", 
        "10.42.68.214", "10.42.70.171", "10.42.70.128", "10.42.65.134", "10.42.69.141", 
        "10.42.70.201", "10.42.70.7", "10.42.70.173", "10.42.70.232", "10.42.70.224",   
        #"10.42.69.223", 
        "10.42.71.3", #"10.42.71.19", 
        #"10.42.70.244", "10.42.71.9",     
        "10.42.67.220", "10.42.71.28", "10.42.65.78", "10.42.71.4",          
        ]

#sync_and_clear(hosts)
hosts = hosts[:15]
#datasampling(hosts)
run(hosts, "cd FL_Architecture; ./client-ext.sh fl_ok 4")



