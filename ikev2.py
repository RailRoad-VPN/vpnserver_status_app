import json
import subprocess
from pprint import pprint


def random_with_n_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    from random import randint
    return randint(range_start, range_end)


# print(f"call strongswan statusall")
result = str(subprocess.check_output(["/usr/sbin/strongswan", "statusall"]))
result = str(result).split("\\n")

found_user = False
next_ip_adress = False

data = {
    'server': {}
}
users = []
user = {}
for line in result:
    if next_ip_adress:
        next_ip_adress = False
        server_ip_addr = line
        data['server']['ip_addr'] = server_ip_addr.split(" ")[-1]

    if "Listening IP addresses" in line:
        next_ip_adress = True

    if "Security Associations" in line:
        users_count = line.split("Associations")[-1].split(",")[0].split("(")[1].split(' ')[0]
        data['server']['users_count'] = users_count
        # print(f"Users Connected to server: {users_count}")

    if "ESTABLISHED" in line and not found_user:
        found_user = True
        user = {}
        info = line.split("ESTABLISHED")[1].split(",")
        time_connected = info[0]
        user['time_connected'] = time_connected
        # print(f"Time Connected: {time_connected}")
        ip_device = info[1].split("...")[-1].split("[")[0]
        email = info[1].split("...")[-1].split("[")[1].split("]")[0]
        user['ip_device'] = ip_device
        user['email'] = email
        # print(f"User IP address: {ip_device}")
        # print(f"User Email: {email}")

    if "rekeying in" in line:
        bytes_i = line.split("bytes_i")[0].split(", ")[-1]
        # print(f"bytes_i: {bytes_i}")
        user['bytes_i'] = bytes_i
        bytes_o = line.split("bytes_o")[0].split(", ")[-1]
        # print(f"bytes_o: {bytes_o}")
        user['bytes_o'] = bytes_o
        found_user = False
        users.append(user)
        user = {}

data['users'] = users

pprint(data)

users_json = json.dumps(data)
