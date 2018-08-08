import os
import subprocess
from pprint import pprint


def random_with_n_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    from random import randint
    return randint(range_start, range_end)


log_file_name = f"/root/{str(random_with_n_digits(3))}_statusall.log"

print(f"call strongswan statusall")
result = subprocess.check_output(["/usr/sbin/strongswan", "statusall"])
print(f"result: {result}")

f = open(log_file_name, "w")
f.write(str(result))
f.close()

f = open(log_file_name, 'r')
res = f.readlines()
f.close()

found_user = False

users = []
for line in res:
    if "Security Associations" in line:
        users_count = line.split("Associations")[-1].split(",")[0].split("(")[1].split(' ')[0]
        #print(f"Users Connected to server: {users_count}")
    if "ESTABLISHED" in line and not found_user:
        found_user = True
        user = {}
        info = line.split("ESTABLISHED")[1].split(",")
        time_connected = info[0]
        user['time_connected'] = time_connected
        #print(f"Time Connected: {time_connected}")
        ip_device = info[1].split("...")[-1].split("[")[0]
        email = info[1].split("...")[-1].split("[")[1].split("]")[0]
        user['ip_device'] = ip_device
        user['email'] = email
        #print(f"User IP address: {ip_device}")
        #print(f"User Email: {email}")
    if "rekeying in" in line:
        bytes_i = line.split("bytes_i")[0].split(", ")[-1]
        #print(f"bytes_i: {bytes_i}")
        user['bytes_i'] = bytes_i
        bytes_o = line.split("bytes_o")[0].split(", ")[-1]
        #print(f"bytes_o: {bytes_o}")
        user['bytes_o'] = bytes_o
        found_user = False
        users.append(user)
        user = {}

pprint(users)

os.remove(log_file_name)
