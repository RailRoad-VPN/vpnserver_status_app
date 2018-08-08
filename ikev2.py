import json
import os
import subprocess
from pprint import pprint


def random_with_n_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    from random import randint
    return randint(range_start, range_end)


result = str(subprocess.check_output(["/usr/sbin/strongswan", "statusall"]))
result = str(result).split("\\n")

# f = open("/Users/dikkini/Developing/workspaces/my/DFN/vpnserver_status_app/ikev2.log", 'r')
# result = f.readlines()
# f.close()

found_user = False
next_ip_adress = False
was_rekey = False

email = None

data = {
    'server': {
        'uuid': os.environ['RROADVPN_SERVER_UUID'],
        'type': 'ikev2'
    }
}

users = {}
user = {}
for line in result:
    if next_ip_adress:
        next_ip_adress = False
        server_ip_addr = line
        data['server']['ip_addr'] = server_ip_addr.split("\n")[0].split(" ")[-1]
        continue

    if "Listening IP addresses" in line:
        next_ip_adress = True
        continue

    if "Security Associations" in line:
        users_count = line.split("Associations")[-1].split(",")[0].split("(")[1].split(' ')[0]
        data['server']['users_count'] = users_count
        continue

    if "ESTABLISHED" in line and not found_user:
        found_user = True
        user = {}
        info = line.split("ESTABLISHED")[1].split(",")
        time_connected = info[0]
        user['time_connected'] = time_connected
        ip_device = info[1].split("...")[-1].split("[")[0]
        email = info[1].split("...")[-1].split("[")[1].split("]")[0]
        user['ip_device'] = ip_device
        user['email'] = email
        continue

    if "rekeying in" in line:
        bytes_i = line.split("bytes_i")[0].split(", ")[-1].split(' ')[0]
        user['bytes_i'] = bytes_i
        bytes_o = line.split("bytes_o")[0].split(", ")[-1].split(' ')[0]
        user['bytes_o'] = bytes_o
        found_user = False
        was_rekey = True
        continue

    if was_rekey:
        was_rekey = False
        virtual_ip = line.split(" === ")[-1].split("/32")[0]
        user['virtual_ip'] = virtual_ip
        users[email] = user
        user = {}
        continue

data['users'] = users

pprint(data)

users_json = json.dumps(data)
