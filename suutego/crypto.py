""" Filename: crypto.py

    Purpose: The application agnostic solution to perform encryption/decryption

    @author Albert Jiro Hynes
"""

def calc_crypto_seed(layers : list, password):
    """ Calculate the PRNG crypto seed (hash) with the height and width of each layer
        OR password if applicable (maybe remove)

        @param layers   - list of dictionaries of bytestrings and positions in image
    """
    return None

def encode(seed, route : list, message : str):
    """ Encode the message into the layers

        @param seed     - 
        @param route    - 
        @param message  - 
    """
    return None

def decode(seed, route : list):
    """ Decode the message from the layers
    """
    decoded_message = ""
    return decoded_message