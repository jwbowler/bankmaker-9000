import socket

class mysocket:

    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock
        self.buf = ""

    def connect(self, host, port):
        self.sock.connect((host, port))

    def mysend(self, msg):
        self.sock.send(msg)

    def myreceive(self):
        data = ''
	message = ''
        while True:
          data += self.sock.recv(1024)
          if not data:
            break
          self.buf += data
          if '\n' not in self.buf:
            message += self.buf
            self.buf = ''
          else:
            message, self.buf = self.buf.split('\n', 1)
            return message

s = mysocket()
s.connect('10.0.207.145', 25000)
s.mysend('{"type": "hello", "team": "FOO"}\n')
print s.myreceive()
