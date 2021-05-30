from peer_info import *
import socket
import types
import json
import hashlib
import ast
from gen_chain import *
import peer_DHTS
from importlib import reload
import FILE_LIST



def add(file_path="./", is_from_sys=False, sys_dict={}, sys_OID=""):
    reload(peer_DHTS)
    reload(FILE_LIST)
    old_ddt =  peer_DHTS.DDT
    OID = None
    if not is_from_sys:
        chain, OID = get_chain(file_path)
        old_ddt.update(chain)
        update_file_sys({OID: "".join(str(tmp) for tmp in chain[OID][1][:2])})
    else:
        OID = sys_OID
        old_ddt.update(sys_dict)
        update_file_sys({OID: "".join(str(tmp) for tmp in sys_dict[OID][1][:2])})
    with open("peer_DHTS.py",'w') as f:
        f.write("DDT="+str(old_ddt))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((GENESIS_HOST, GENESIS_PORT))
        sock.sendall(json.dumps({'type': 'add', 'OID': OID, 'peerID':peerID}).encode('utf-8'))
    print("Successfully added OID:{}".format(OID))

def get(OID):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((GENESIS_HOST, GENESIS_PORT))
    s.sendall(json.dumps({'type':"ask", "OID": OID, "peerID":peerID}).encode('utf-8'))
    data = s.recv(1024).decode('utf-8')
    HOST, PORT = eval(data)
    print(data)
    s.close()
    reload(peer_DHTS)
    reload(FILE_LIST)
    if OID in peer_DHTS.DDT:
        print("FILE EXISTS, USE FLASH TO ACCESS IT")
        return
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    s.connect((HOST, PORT))
    PH, PP = s.getsockname()
    s.send(json.dumps({'type':'get', 'OID': [OID]}).encode('utf-8'))
    data = s.recv(1024)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    eval_lis = eval(data.decode('utf-8'))
    s.sendall(json.dumps({'type':'get', 'OID': eval_lis[1][2:]}).encode('utf-8'))
    data = s.recv(4096)
    print(eval(data.decode('utf-8').replace("][", "],[")))
    a = eval(data.decode('utf-8').replace("][", "],["))

    dat_dict = {}
    for x in range(len(eval_lis[1][2:])):
        dat_dict[eval_lis[1][2:][x]] = a[x]

    dat_dict[OID] = eval_lis
    print(dat_dict)
    add(is_from_sys=True, sys_dict=dat_dict, sys_OID=OID)

def remove(OID):
    reload(FILE_LIST)
    if OID not in peer_DHTS.DDT:
        print("THE FILE DOES NOT EXIST")
        return
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((GENESIS_HOST, GENESIS_PORT))
    s.sendall(json.dumps({'type':'del', 'OID':OID, "peerID":peerID}).encode('utf-8'))
    s.close()
    old_ddt = peer_DHTS.DDT
    del_list = old_ddt[OID][1][2:]+[OID]
    [old_ddt.pop(oid) for oid in del_list]
    FILE_LIST.FILE_LIST.pop(OID)
    update_file_sys(FILE_LIST.FILE_LIST, False)
    with open("peer_DHTS.py",'w') as f:
        f.write("DDT="+str(old_ddt))

def show_files():
    reload(FILE_LIST)
    print(json.dumps(FILE_LIST.FILE_LIST))

def update_file_sys(dat, update=True):
    old_dat = FILE_LIST.FILE_LIST
    if update: old_dat.update(dat)
    with open("FILE_LIST.py", 'w') as f:
        f.write("FILE_LIST="+str(old_dat))

#add("./hell.txt")
print(show_files())
print("Received", 1024)