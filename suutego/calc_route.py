""" Filename: calc_route.py

    Purpose: calculates a psuedorandom path

    @author Albert Jiro Hynes
"""

from . import hill
import numpy as np

def calc_paint_layers(layers : dict, local_id_map : dict, color_space : str):
    """ This function takes info needed to perform HILL on paint layers

        @param layers       - dict of dictionaries of bytestrings + positions in image {bytes,x,y,w,h,id}
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


def calc_route(buckets : dict, seed : int):
    """ This function scrambles "best", "next best", "ok", "next ok" buckets

        Traversals will go in that order, but the traversal in each bucket
        is randomized

        @param buckets - buckets to scramble
        @param seed    - seed for PRNG scrambling
    """
    # initialize the route
    route = []
    scrambled_parts = []

    # start the rng
    prng = np.random.default_rng(seed)

    # helper function to scramble our buckets
    def scramble_bucket(bucket):
        return prng.permutation(bucket)

    # for each type of bucket now, in order
    for key in ["best", "next_best", "ok", "next_ok"]:
        if(len(buckets[key]) > 0):
            scrambled_parts.append(scramble_bucket(buckets[key]))

    # safely stack it up now, if there is anything
    route = np.vstack(scrambled_parts) 

    return route
