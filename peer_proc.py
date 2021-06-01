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
import sys
from multiprocessing import Process
from multiprocessing import Manager
import numpy as np

help_string = '''
usage: peer_proc.py [add <path>]
                    [del <OID>]
                    [show_files()]
                    [download <OID> optional: <path>]
                    [get <OID>]
                    [--factory-reset]
'''

def add(file_path="./", is_from_sys=False, sys_dict={}, sys_OID=""):
    reload(peer_DHTS)
    reload(FILE_LIST)
    old_ddt =  peer_DHTS.DDT
    OID = None
    if not is_from_sys:
        chain, OID = get_chain(file_path)
        if OID in peer_DHTS.DDT:
            print("FILE EXISTS, USE FLASH TO ACCESS IT")
            return
        old_ddt.update(chain)
        update_file_sys({OID: ".".join(str(tmp) for tmp in chain[OID][1][:2])})
    else:
        OID = sys_OID
        if OID in peer_DHTS.DDT:
            print("FILE EXISTS, USE FLASH TO ACCESS IT")
            return
        old_ddt.update(sys_dict)
        update_file_sys({OID: "".join(str(tmp) for tmp in sys_dict[OID][1][:2])})
    with open("peer_DHTS.py",'w') as f:
        f.write("DDT="+str(old_ddt))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((GENESIS_HOST, GENESIS_PORT))
        sock.sendall(json.dumps({'type': 'add', 'OID': OID, 'peerID':peerID}).encode('utf-8'))
    print("Successfully added OID:{}".format(OID))

def get(OID):
    if OID in peer_DHTS.DDT:
        print("FILE EXISTS, USE FLASH TO ACCESS IT")
        return
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((GENESIS_HOST, GENESIS_PORT))
    s.sendall(json.dumps({'type':"ask", "OID": OID, "peerID":peerID}).encode('utf-8'))
    data = s.recv(1024).decode('utf-8')
    #print(eval(data))
    HOST, PORT = eval(data)[0]
    prs = data
    s.close()
    reload(peer_DHTS)
    reload(FILE_LIST)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    s.connect((HOST, PORT))
    PH, PP = s.getsockname()
    s.send(json.dumps({'type':'get', 'OID': [OID]}).encode('utf-8'))
    data = s.recv(1024)
    s.close()
    eval_lis = eval(data.decode('utf-8'))
    chunk_lis = np.array(eval_lis[1][2:])
    chunk_lis = np.array_split(chunk_lis, len(eval(prs)))
    chunk_lis = [list(k) for k in chunk_lis]
    manager = Manager()
    dat_dict = manager.dict()
    def peer_dist_get(clis, addr, dat_dict):
        sockk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sockk.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sockk.connect((addr[0], addr[1]))
        #print(clis)
        sockk.sendall(json.dumps({'type':'get', 'OID': clis}).encode('utf-8'))
        data = sockk.recv(4096)
        #print(eval(data.decode('utf-8').replace("][", "],[")))
        a = eval(data.decode('utf-8').replace("][", "],["))
        #print(a)
        for x in range(len(clis)):
            dat_dict[clis[x]] = a[x]
        #print(dat_dict)
        sockk.close()
    #print("\nmanaeger:\n{}".format(dat_dict.values()))
    multi_proc = []
    #print("\n\n")
    #print(chunk_lis)
    for (chunk, pr) in zip(chunk_lis, eval(prs)):
        print("{} type: {}".format(chunk, type(chunk)))
        print("{} type: {}".format(pr, type(pr)))
        multi_proc.append(Process(target=peer_dist_get, args=(chunk, pr, dat_dict,)))
        multi_proc[len(multi_proc)-1].start()
        multi_proc[len(multi_proc)-1].join()

    dat_dict[OID] = eval_lis
    #print(dat_dict)
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

def download_exec_file(OID, dest="./"):
    gen_file(OID, peer_DHTS.DDT, dest_path=dest)

def format_peer():
    with open("FILE_LIST.py", 'w') as f:
        f.write("FILE_LIST={}")
    with open("peer_DHTS.py", 'w') as f:
        f.write("DDT={}")

if len(sys.argv) < 2:
    print(help_string)
    sys.exit(1)

if (sys.argv[1] == 'add'):
    if (len(sys.argv) < 3):
        print("usage:", sys.argv[0], "[add <path>]")
        sys.exit(1)
    else:
        add(sys.argv[2])
elif (sys.argv[1] == 'show_files'):
    show_files()
elif (sys.argv[1] == "del"):
    if (len(sys.argv) != 3):
        print("usage:", sys.argv[0], "[del <path>]")
        sys.exit(1)
    else:
        remove(sys.argv[2])
elif (sys.argv[1] == 'download'):
    if (len(sys.argv) < 3):
        print("usage:", sys.argv[0], "[download <OID> optional: <path>]")
        sys.exit(1)
    else:
        if (len(sys.argv) == 4):
            download_exec_file(sys.argv[2], sys.argv[3])
        else:
            download_exec_file(sys.argv[2])
elif (sys.argv[1] == 'get'):
    if (len(sys.argv) < 3):
        print("usage:", sys.argv[0], "[get <OID>]")
        sys.exit(1)
    else:
        get(sys.argv[2])
elif (sys.argv[1] == '--factory-reset'):
    format_peer()
else:
    print(help_string)
