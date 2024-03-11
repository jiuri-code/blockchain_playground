#!/usr/bin/python
# protocol ref@ https://en.bitcoin.it/wiki/Protocol_documentation
# transaction ref@ https://en.bitcoin.it/wiki/Transaction
# script ref@ https://en.bitcoin.it/wiki/Script
import base58
import binascii

def change_endianness(x):
    # type x: hex str
    # rtype: hex str

    # If there is an odd number of elements, we make it append 0
    if (len(x) % 2) == 1:
        x += "0"

    # change str to byte obj
    byte_obj = bytes.fromhex(x)

    # convert BE to LE
    byte_obj_le = int.from_bytes(byte_obj, byteorder='little')

    # convert byte obj to hex str
    hex_str = format(byte_obj_le, 'x')

    return hex_str

def parse_tx_str(tx, size):
    # return slice of TX byte flow
    element = tx.hex[tx.offset:tx.offset+size*2]
    tx.offset += size * 2
    return element

def parse_varint(tx):
    data = tx.hex[tx.offset:]
    assert(len(data) > 0)
    size = int(data[:2], 16)
    assert(size <= 255)

    if size <= 0xfc:  # No prefix
        storage_length = 1
        varint = data[:storage_length * 2]
        tx.offset += storage_length * 2
        return varint
    elif size == 0xfd:  # 0xFD
        storage_length = 3
    elif size == 0xfe:  # 0xFE
        storage_length = 5
    elif size == 0xff:  # 0xFF
        storage_length = 9
    else:
        raise Exception("Wrong input data size")

    varint = data[2:storage_length * 2]
    tx.offset += storage_length * 2

    return varint

def script_to_address(script):
    def get_address_from_script(script_hex, version_byte):
        address_with_version = version_byte + script_hex
        bitcoin_address = base58.b58encode_check(binascii.unhexlify(address_with_version)).decode('utf-8')
        return bitcoin_address

    # P2PKH
    if script.startswith('76a914') and script.endswith('88ac'):
        return get_address_from_script(script[6:-4], '00')
    
    # P2SH 
    # P2SH-P2WSH: using hash160 to encode P2WSH
    # P2SH-P2WPKH: using hash160 to encode P2WPKH
    # P2SH-P2WSH and P2SH-P2WPKH can be used in P2SH
    if script.startswith('a914') and script.endswith('87'):
        return get_address_from_script(script[4:-2], '05')
    
    # P2WPKH
    if script.startswith('0014'):
        return get_address_from_script(script[4:], '00')
    
    # P2WSH
    if script.startswith('0020'):
        return get_address_from_script(script[4:], '00')

class TX:
    def __init__(self):
        self.version = None
        self.witness = None
        self.inputs = None
        self.outputs = None
        self.nLockTime = None
        self.prev_tx_id = []
        self.prev_out_index = []
        self.scriptSig = []
        self.scriptSig_len = []
        self.nSequence = []
        self.value = []
        self.scriptPubKey = []
        self.scriptPubKey_len = []
        self.dst_address = []

        self.offset = 0
        self.hex = ""
        
    def deserialize(cls, hex_tx):
        tx = cls()
        tx.hex = hex_tx
        tx.version = int(change_endianness(parse_tx_str(tx, 4)), 16)

        # check tx_witness, if present, always 0001
        # if parse_tx_str(tx, 2) == "0001":
        #     tx.witness = True
        #     print("witness")
        # else:
        #     tx.witness = False
        #     tx.offset -= 2 * 2

        # INPUTS
        tx.inputs = int(parse_varint(tx), 16)

        for i in range(tx.inputs):
            tx.prev_tx_id.append(change_endianness(parse_tx_str(tx, 32)))
            tx.prev_out_index.append(int(change_endianness(parse_tx_str(tx, 4)), 16))

            # ScriptSig
            tx.scriptSig_len.append(int(parse_varint(tx), 16))
            tx.scriptSig.append(parse_tx_str(tx, tx.scriptSig_len[i]))
            tx.nSequence.append(int(change_endianness(parse_tx_str(tx, 4)), 16))

        # OUTPUTS
        tx.outputs = int(parse_varint(tx), 16)

        for i in range(tx.outputs):
            tx.value.append(int(change_endianness(parse_tx_str(tx, 8)), 16))

            # ScriptPubKey
            tx.scriptPubKey_len.append(int(parse_varint(tx), 16))
            tx.scriptPubKey.append(parse_tx_str(tx, tx.scriptPubKey_len[i]))
            tx.dst_address.append(script_to_address(tx.scriptPubKey[i]))
            
        # if tx.witness == True:
        #     parse_tx_str(tx, 2)

        tx.nLockTime = int(change_endianness(parse_tx_str(tx, 4)), 16)

        if tx.offset != len(tx.hex):
            raise Exception("There is some error in the serialized transaction passed as input")
        else:
            tx.offset = 0

        return tx

    def display_info(tx):
        tx_info = {}
        tx_info["version"] = tx.version
        tx_info["input_num"] = tx.inputs
        tx_info["inputs"] = []
        tx_info["output_num"] = tx.outputs
        tx_info["outputs"] = []

        for i in range(tx.inputs):
            tx_info["inputs"] .append({
                "outpoint": {
                    "hash": tx.prev_tx_id[i],
                    "index": tx.prev_out_index[i]
                },
                "script": tx.scriptSig[i],
                "sequence": tx.nSequence[i]
            })

        for i in range(tx.outputs):
            tx_info["outputs"] .append({
                "value": tx.value[i],
                "script": tx.scriptPubKey[i],
                "address": tx.dst_address[i]
            })
        
        tx_info["lock_time"] = tx.nLockTime

        print(tx_info)
