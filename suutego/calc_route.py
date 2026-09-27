""" Filename: calc_route.py

    Purpose: The application agnostic solution to calculate a path

    @author Albert Jiro Hynes
"""

from . import hill
import hashlib

def calc_route(layers : list, width : int, height : int, color_space : str, seed_plus : list = None):
    """ This function takes info needed to calculate a nice route

        @param layers       - list of dictionaries of bytestrings + positions in image {bytes,x,y,w,h,id}
        @param width        - width of the wider image
        @param height       - height of the wider image
        @param color_space  - could be RGBA or CMYKA or more
        @param seed_plus    - if desired, more things to add to the seed
    """
    # calculate pixels/layers we CAN change, and then pixels we shouldn't
    maps, num_best, num_ok = hill.HILL_algo(layers, color_space)
    
    # obtain traversal seed
    traversal_seed = calc_traversal_seed(layers)

    # return the traversal seed + possible stuff to do
    return maps, traversal_seed, num_best, num_ok

def calc_traversal_seed(layers : list, seed_plus : list = None):
    """ Calculate the PRNG traversal seed (hash)

        At minimum this uses the starting x/y, width/height, and id of each
        layer, but other attrs may also be considered.

        @param layers    - list of dictionaries of bytestrings and positions in image
        @param seed_plus - list of additional attrs to be used in seed generation
    """
    seed_components = []
    
    for layer in layers:
        seed_components.append(f"node {layer["id"]}:{layer["width"]}x{layer["height"]}:{layer["x"]},{layer["y"]}")

    # create deterministic sha-256 hash
    raw_key = "|".join(seed_components).encode('utf-8')
    hash_digest = hashlib.sha256(raw_key).digest()

    # create seed
    seed = int.from_bytes(hash_digest[:8], byteorder='big')

    return seed


