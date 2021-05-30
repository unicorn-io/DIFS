import sys
import socket
import types
import selectors
import traceback
#from peer_DHTS import DDT
import peer_DHTS
import json
import ast
from importlib import reload
import hashlib

GENESIS_HOST = '192.168.100.107'
GENESIS_PORT = 65000

PEER_HOST = ""
PEER_PORT = -1
OLD_PORT= -1

sel = selectors.DefaultSelector()

def accept_wrapper(sock):
    conn, addr = sock.accept()
    print("accepted connection from ", addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        try:
            recv_data  = sock.recv(4096)
            if recv_data:
                print(recv_data.decode('utf-8').strip())
                print(type(recv_data.decode('utf-8')))
                dat = json.loads(recv_data.decode('utf-8').strip().replace("\'", "\""))
                if (dat['type'] == 'get'):
                    if mask & selectors.EVENT_WRITE:
                        reload(peer_DHTS)
                        req_lis = dat['OID']
                        d = b''
                        for x in range(len(req_lis)):
                            print("-----------Sending Chunk({}/{})".format(x+1, len(req_lis)))
                            d += str(peer_DHTS.DDT[req_lis[x]]).encode('utf-8')
                        sock.sendall(d)
                        
            else:
                print("closing connection to", data.addr)
                sel.unregister(sock)
                sock.close()
        except:
            pass


def init():
    global PEER_PORT, PEER_HOST
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect((GENESIS_HOST, GENESIS_PORT))
        PEER_HOST, PEER_PORT = s.getsockname()
        with open("peer_info.py", 'w') as cons_file:
            cons_file.write("GENESIS_HOST='{}'\n".format(GENESIS_HOST))
            cons_file.write("GENESIS_PORT={}\n".format(GENESIS_PORT))
            cons_file.write("PEER_HOST='{}'\n".format(PEER_HOST))
            cons_file.write("PEER_PORT='{}'\n".format(PEER_PORT))
            cons_file.write("peerID='{}'\n".format(hashlib.sha256(str(s.getsockname()).encode('utf-8')).hexdigest()))
        s.shutdown(socket.SHUT_RDWR)
        s.close()

init()
peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(PEER_HOST, PEER_PORT)
peer_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
peer_sock.bind((PEER_HOST, PEER_PORT))
peer_sock.listen()
print("listening on ", (PEER_HOST, PEER_PORT))
peer_sock.setblocking(False)
sel.register(peer_sock, selectors.EVENT_READ, data=None)

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                service_connection(key, mask)
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()



