""" Filename: calc_route.py

    Purpose: calculates a psuedorandom path

    @author Albert Jiro Hynes
"""

from . import hill
import hashlib
import numpy as np

def calc_paint_layers(layers : list, local_id_map : dict, color_space : str):
    """ This function takes info needed to perform HILL on paint layers

        @param layers       - list of dictionaries of bytestrings + positions in image {bytes,x,y,w,h,id}
        @param local_id_map - map of local to string IDs
        @param width        - width of the wider image
        @param height       - height of the wider image
        @param color_space  - could be RGBA or CMYKA or more
    """
    # calculate pixels/layers we CAN change, and then pixels we shouldn't
    paint_layer_buckets = hill.HILL_algo(layers, local_id_map, color_space)

    # return the buckets of edits to make
    return paint_layer_buckets


def calc_vector_layers(layers : list, color_space : str):
    """ This function takes info needed to identify vector changes

        @param layers       - list of dictionaries of layer IDs to SVGs
        @param color_space  - could be RGBA or CMYKA or more
    """
    return None


def calc_traversal_seed(layer_lists : list):
    """ Calculate the PRNG traversal seed (hash)

        At minimum this uses the starting x/y, width/height, and id of each
        paint layer, but other attrs may also be considered.

        @param layers    - list of dictionaries of bytestrings and positions in image
        @param seed_plus - list of additional attrs to be used in seed generation
    """
    seed_components = []
    
    for layer in layer_lists:
        seed_components.append(f"node {layer["id"]}:{layer["width"]}x{layer["height"]}:{layer["x"]},{layer["y"]}")

    # create deterministic sha-256 hash
    raw_key = "|".join(seed_components).encode('utf-8')
    hash_digest = hashlib.sha256(raw_key).digest()

    # create seed
    seed = int.from_bytes(hash_digest[:8], byteorder='big')

    return seed


def calc_route():
    return

