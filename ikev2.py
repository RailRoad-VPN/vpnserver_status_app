import json
import os
import subprocess
import uuid
from pprint import pprint

import requests

from utils import random_x, get_unixtime


def gen_sec_token() -> str:
    # print('---------------- gen token')
    token = ""
    ruuid = str(uuid.uuid4())
    ruuid = ruuid.replace("-", "")
    ruuid_len = len(ruuid)
    r4 = str(random_x(1, ruuid_len))
    token += ruuid
    unixtime = get_unixtime()
    # print("Unix time:" + str(unixtime))
    # print("Unix time len:" + str(len(str(unixtime))))
    unixtime_divided = int(unixtime) / int(r4)
    # print("Unix time divided:" + str(unixtime_divided))
    unixtime_divided_rounded = "%.10f" % (unixtime_divided)
    # print("Unix time divided rounded:" + str(unixtime_divided_rounded))
    unixtime_divided_len = str(len(str(unixtime_divided_rounded)))
    if len(unixtime_divided_len) == 1:
        unixtime_divided_len = "0" + str(unixtime_divided_len)
    # print("Unix time rounded len:" + unixtime_divided_len )
    left_token = token[:int(r4)]
    center_token = str(unixtime_divided_rounded)
    right_token = token[int(r4):]
    token = left_token + center_token + right_token
    if len(r4) == 1:
        r4 = "0" + str(r4)
    token = str(r4) + str(unixtime_divided_len) + token
    # print("Random number:" + str(r4))
    # print("Token: " + str(token))
    return token


api_host = "http://rroadvpn.net:61885"
resource_uri = "api/v1/vpns/servers"
headers = {
    'Content-Type': 'application/json',
    'Accept': 'text/plain'
}

# debian - /usr/sbin/ipsec, centos - /usr/sbin/strongswan
# TODO debian
result = str(subprocess.check_output(["/usr/sbin/strongswan", "statusall"]))
result = str(result).split("\\n")

found_user = False
next_ip_adress = False
was_rekey = False

email = None

# {
# 	'server': {
# 		'ip_addr': '194.87.235.49',
# 		'type': 'ikev2',
# 		'users_count': '1',
# 		'uuid': '123'
# 	},
# 	'users': {
# 		'user1@giftshaker.com': {
# 			'bytes_i': '180731',
# 			'bytes_o': '4756099',
# 			'email': 'user1@giftshaker.com',
# 			'device_ip': '213.87.150.213',
# 			'time_connected': ' 32 minutes ago',
# 			'virtual_ip': '10.10.2.1'
# 		}
# 	}
# }

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
        device_ip = info[1].split("...")[-1].split("[")[0]
        email = info[1].split("...")[-1].split("[")[1].split("]")[0]
        user['device_ip'] = device_ip
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

url = f"{api_host}/{resource_uri}/{data['server']['uuid']}/connections"

f = open('/tmp/ikev2.output', 'wt', encoding='utf-8')
f.write(json.dumps(data))
f.close()

headers['X-Auth-Token'] = gen_sec_token()

try:
    req = requests.post(url=url, json=data, headers=headers)
except requests.exceptions.ConnectionError as e:
    print(f"API error: {e}")
    exit(100)

exit(0)
