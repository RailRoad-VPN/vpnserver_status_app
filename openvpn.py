import json
import os
from pprint import pprint

import requests


def random_with_n_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    from random import randint
    return randint(range_start, range_end)


api_host = "http://internal.novicorp.com:61885"
resource_uri = "api/v1/vpnc/servers"
headers = {
    'Content-Type': 'application/json',
    'Accept': 'text/plain'
}
openvpn_status_file = "/etc/openvpn/openvpn-status.log"

f = open(openvpn_status_file, 'r')
res = f.readlines()
f.close()

client_list_next = False
routing_table_next = False
found_user = False

email = None
users_count = 0

# OpenVPN
# {
# 	'server': {
# 		'type': 'openvpn',
# 		'users_count': 2,
# 		'uuid': '456'
# 	},
# 	'users': {
# 		'mbp': {
# 			'bytes_i': '1164331',
# 			'bytes_o': '13418401',
# 			'connected_since': 'Wed Aug  8 16:27:35 2018',
# 			'email': 'mbp',
# 			'ip_device': '185.89.9.144',
# 			'last_ref': 'Wed Aug  8 16:42:01 2018\n',
# 			'virtual_ip': '10.8.0.2'
# 		},
# 		'test_api': {
# 			'bytes_i': '2571431944',
# 			'bytes_o': '28721319995',
# 			'connected_since': 'Sat Aug  4 18:49:47 2018',
# 			'email': 'test_api',
# 			'device_ip': '109.252.58.250',
# 			'virtual_ip': '10.8.0.5'
# 		}
# 	}
# }


data = {
    'server': {
        'uuid': os.environ['RROADVPN_SERVER_UUID'],
        'type': 'openvpn'
    }
}

users = {}
user = {}
for line in res:
    if "GLOBAL STATS" in line:
        routing_table_next = False
        found_user = False
        break
    if "Common Name,Real Address,Bytes Received,Bytes Sent,Connected Since" in line:
        client_list_next = True
        found_user = True
        continue
    if "ROUTING TABLE" in line:
        client_list_next = False
        found_user = False
        continue
    if client_list_next and found_user:
        users_count += 1
        user_str = line
        user_str_splitted = user_str.split(',')
        email = user_str_splitted[0]
        user['email'] = email
        device_ip = user_str_splitted[1].split(":")[0]
        user['device_ip'] = device_ip
        bytes_i = user_str_splitted[2]
        user['bytes_i'] = bytes_i
        bytes_o = user_str_splitted[3]
        user['bytes_o'] = bytes_o
        connected_since = user_str_splitted[4].split("\n")[0]
        user['connected_since'] = connected_since
        users[email] = user
        user = {}
    if "Virtual Address" in line:
        client_list_next = False
        routing_table_next = True
        found_user = True
        continue
    if routing_table_next and found_user:
        user_route_table_str = line
        user_route_table_str_splitted = user_route_table_str.split(',')
        virtual_ip = user_route_table_str_splitted[0]
        email = user_route_table_str_splitted[1]
        users[email]['virtual_ip'] = virtual_ip

data['server']['users_count'] = users_count
data['users'] = users

pprint(data)

users_json = json.dumps(data)

url = f"{api_host}/{resource_uri}/{data['server']['uuid']}/connections"

f = open('/tmp/openvpn.output', 'wt', encoding='utf-8')
f.write(users_json)
f.close()

try:
    req = requests.post(url=url, json=users_json, headers=headers)
except requests.exceptions.ConnectionError as e:
    print(f"API error: {e}")
    exit(100)

exit(0)
