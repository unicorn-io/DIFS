#!/usr/bin/env python3

import sys
import socket
import selectors
import types
import hashlib
import json

from genesis_DHTS import *

sel = selectors.DefaultSelector()

def accept_wrapper(sock):
    conn, addr = sock.accept()
    print("accepted connection from ", addr)
    conn.setblocking(False)
    peerID = hashlib.sha256(str(addr).encode('utf-8')).hexdigest()
    peer_list[peerID] = addr # laddr field in socket
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data  = sock.recv(4096)
        if recv_data:
            dat = json.loads(recv_data.decode().replace("\'", "\""))
            if (dat['type'] == 'add'):
                if dat['OID'] in dist_data_tab:
                    dist_data_tab[dat['OID']].append(dat['peerID'])
                else:
                    dist_data_tab[dat['OID']] = [dat['peerID']]
                print(dist_data_tab)
                print(peer_list)
            elif (dat['type'] == 'del'):
                try:
                    dist_data_tab[dat['OID']].remove(dat['peerID'])
                    if(len(dist_data_tab[dat['OID']]) ==  0):
                        dist_data_tab.pop(dat['OID'])
                except:
                    print("ARG ERRORS MULTIPLE, CHECK IMPL")
            else:
                if mask & selectors.EVENT_WRITE:
                    print('processing............')
                    print('Sending CONFIG for OID({}) to PEERID: {}'.format(dat['OID'], dat['peerID']))
                    try:
                        print(str(peer_list[dist_data_tab[dat['OID']][0]]))
                        sent = sock.send(str(peer_list[dist_data_tab[dat['OID']][0]]).encode('utf-8'))
                    except:
                        print("KEY ERROR: INVALID QUERY")
        else:
            print("closing connection to", data.addr)
            sel.unregister(sock)
            sock.close()
        

if len(sys.argv) != 3:
    print("usage:", sys.argv[0], "<host> <port>")
    sys.exit(1)

host, port = sys.argv[1], int(sys.argv[2])
lis_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lis_socket.bind((host, port))
lis_socket.listen()
print("listening on ", (host, port))
lis_socket.setblocking(False)
sel.register(lis_socket, selectors.EVENT_READ, data=None)

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
    