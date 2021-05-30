from cryptography.hazmat.primitives.hashes import SHA256, Hash
from cryptography.hazmat.backends import default_backend
from pyrobuf_util import to_varint
import base58
import json
#from DDT import ddt

# OBJECT IDENTIFIER
def gen_OID(data):
    h = Hash(SHA256(), backend=default_backend())
    h.update(data)
    digest = h.finalize()

    hash_function = 0x12 # sha2-256
    length = len(digest)
    multihash = to_varint(hash_function) + to_varint(length) + digest

    return base58.b58encode(bytes(multihash)).decode()

def get_chain(file_path):
    to_ret = {}
    is_genesis = True
    OID_LIST=[]
    with open(file_path, 'rb') as f:
        OID = None
        old_OID=None
        while True:
            tmp_chunk = f.read(256)
            if (tmp_chunk == "".encode('utf-8')):
                break
            if (is_genesis): 
                OID = gen_OID(tmp_chunk)
                is_genesis = False
                to_ret[OID] = [tmp_chunk]
            else:
                OID_LIST.insert(0, OID)
                old_OID = OID
                OID = gen_OID(old_OID.encode('utf-8')+tmp_chunk)
                to_ret[OID] = [old_OID, tmp_chunk]
        OID_LIST.insert(0, OID)
        OID_LIST.insert(0, file_path.split('.')[-1])
        OID_LIST.insert(0, file_path.split('.')[-2])
        old_OID = OID
        OID = gen_OID(old_OID.encode('utf-8')+str(OID_LIST).encode('utf-8'))
        to_ret[OID] = [old_OID, OID_LIST]
    return to_ret, OID

def gen_file(OID, chain, dest_path="./"):
    OID_LIST = chain[OID][1]
    loc = dest_path+OID_LIST[0].split("/")[-1]+"."+OID_LIST[1]
    with open(loc, 'wb') as f:
        f.write(recursive_data_aggregate(chain, OID_LIST[2:]))
    

def recursive_data_aggregate(chain, oid_list):
    oid_list.reverse()
    data = chain[oid_list[0]][0]
    for oid in oid_list[1:]:
        data += chain[oid][1]
    return data

#print(get_chain('./hell.txt'))