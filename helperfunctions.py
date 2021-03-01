import json

colorpalette = [(255,0,0),(0,255,0),(0,0,255),
                (255,255,0),(0,255,255),
                (255,0,255),(128,128,128),
                (128,0,0),(128,128,0),
                (0,128,0),(128,0,128),
                (0,128,128),(0,0,128)]


def create_JSONRPC_errormessage(code_arg: int, message_arg: str, data_arg = None, id_arg = None) -> str:
    """
    It's not quite clear how to deal with IDs yet, so we will always send ID null for now.
    """
    data_dict = {
        "jsonrpc": "2.0",
        "error": {
            "code": code_arg,
            "message": message_arg,
            "data": data_arg
        },
        "id": id_arg
    }
    return json.dumps(data_dict)

def create_JSONRPC_responsemessage(result_arg: dict, id_arg = None) -> str:
    """
    TODO: create this response processor
    """
    data_dict = {
        "jsonrpc":"2.0",
        "result":result_arg,
        "id": id_arg
    }
    return json.dumps(data_dict)

def send_TCPIP_message(socket_to_send,message_string,isPreamblePresent,encoding = "utf-8"):
    # TODELETE
    print("from helperfunctions send_TCPIP_message: type(socket_to_send): {}".format(type(socket_to_send)))
    if isPreamblePresent is True:
        message_encoded = message_string.encode(encoding = encoding)
        message_len = len(message_encoded)
        preamble_str = "{:08d}".format(message_len)
        preamble_encoded = preamble_str.encode(encoding = encoding)
        full_msg_encoded = preamble_encoded + message_encoded
        socket_to_send.sendall(full_msg_encoded)
    else:
        message_encoded = message_string.encode(encoding = encoding)
        socket_to_send.sendall(message_encoded)



