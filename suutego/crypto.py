""" Filename: crypto.py

    Purpose: The application agnostic solution to perform encryption/decryption

    @author Albert Jiro Hynes
"""

def encode(seed, layer_lists : list, message : str):
    """ Encode the message into the layers

        @param seed         - PRNG seed
        @param layer_lists  - list of lists, varies by layer type
        @param message      - the message to embed
    """
    return None


def convert_message_to_utf8(message):
    return None

def convert_bytes_to_message(bytes):
    return None

def decode(seed, route : list):
    """ Decode the message from the layers
    """
    decoded_message = ""
    return decoded_message