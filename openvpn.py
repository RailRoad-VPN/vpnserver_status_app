import json
import os
from pprint import pprint


def random_with_n_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    from random import randint
    return randint(range_start, range_end)


openvpn_status_file = "/etc/openvpn/openvpn-status.log"

f = open(openvpn_status_file, 'r')
res = f.readlines()
f.close()

client_list_next = False
routing_table_next = False
found_user = False

email = None
users_count = 0

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
        ip_device = user_str_splitted[1].split(":")[0]
        user['ip_device'] = ip_device
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
        last_ref = user_route_table_str_splitted[3]
        users[email]['virtual_ip'] = virtual_ip
        users[email]['last_ref'] = last_ref

data['server']['users_count'] = users_count
data['users'] = users

pprint(data)

users_json = json.dumps(data)