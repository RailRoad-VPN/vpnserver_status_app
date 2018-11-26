import json
import os
import uuid
from pprint import pprint

import requests

from utils import get_unixtime, random_x


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

url = f"{api_host}/{resource_uri}/{data['server']['uuid']}/connections"

f = open('/tmp/openvpn.output', 'wt', encoding='utf-8')
f.write(json.dumps(data))
f.close()

headers['X-Auth-Token'] = gen_sec_token()

try:
    req = requests.post(url=url, json=data, headers=headers)
except requests.exceptions.ConnectionError as e:
    print(f"API error: {e}")
    exit(100)

exit(0)
