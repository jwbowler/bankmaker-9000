import json
import socket

TCP_IP = '10.0.207.145'
TCP_PORT = 25000
BUFFER_SIZE = 1024
TEAM_NAME = "FOO"
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
request = json.dumps({\
            "type": "hello", \
            "team": TEAM_NAME }) + "\n"
s.send(request)
res = s.recv(BUFFER_SIZE)
print res
s.close()
