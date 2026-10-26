""" Filename: calc_route.py

    Purpose: calculates a psuedorandom path

    @author Albert Jiro Hynes
"""

import numpy as np

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
