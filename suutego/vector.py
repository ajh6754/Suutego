""" 
Filename: vector.py

This file takes SVG representations and finds what to alter in d path

@author Albert Jiro Hynes
"""

import re
import numpy as np

def calc_vector_layers(layers : dict, local_id_map : dict):
    """ This function takes info needed to identify vector changes

        @param layers       - list of dictionaries of layer IDs to svgs
        @param local_id_map - map of local to string IDs
    """
    # identify buckets
    best_bucket = []
    ok_bucket = []
    next_ok_bucket = []

    # regex 1: find <path> tags and grab the 'd' attribute string
    path_regex = re.compile(r'<path[^>]*d="([^"]+)"')

    # regex 2: tokenize the 'd' string into commands or numbers
    token_regex = re.compile(r'([a-zA-Z])|([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)')

    total_floats_evaluated = 0
    discarded_count = 0

    # iterate through each vector layer
    for key in layers.keys():

        # get svg
        svg = layers[key]["svg"]

        # get our local id
        local_id = local_id_map[key]

        # iterate through each shape
        # find the C, c, S, s, Q, and q commands within the path
        # add a few checks to make sure we're only taking good ones

        for shape_idx, path_match in enumerate(path_regex.finditer(svg)):
            d_string = path_match.group(1)
            d_offset = path_match.start(1) 

            # track what command we'er at and then what number index we're at
            current_cmd = ''
            arg_index = 0

            # iterate through every letter and number
            for token_match in token_regex.finditer(d_string):
                cmd = token_match.group(1)
                num = token_match.group(2)

                # if we hit a letter, update state and reset counters
                if(cmd):
                    current_cmd = cmd
                    arg_index = 0

                # if we have a number, see if we can use it
                elif(num):
                    arg_index += 1
                    total_floats_evaluated += 1
                    is_control_point = False

                    # cubic beziers have 6 args, but arg 5/6 are anchor points
                    # so we do not want to edit them
                    if(current_cmd in ['C', 'c']):
                        if((arg_index % 6) in [1, 2, 3, 4]):
                            is_control_point = True

                    # smooth/quadratic beziers have 4 args per curve, but
                    # args 3/4 are the anchor points so don't touch
                    elif(current_cmd in ['S', 's', 'Q', 'q']):
                        if((arg_index % 4) in [1, 2]):
                            is_control_point = True

                    # if we've got a valid number see if it's worth editing
                    if(is_control_point):
                        # filter and discard

                        # we do not want to deal with scientific notation
                        if('e' in num.lower()):
                            discarded_count += 1
                            continue

                        # we don't want to alter pure ints
                        if('.' not in num):
                            discarded_count += 1
                            continue

                        # we don't want clean ending decimals
                        if(num.endswith('.0') or num.endswith('.5') or num.endswith('.25')):
                            discarded_count += 1
                            continue

                        # we don't want near-zero values since changes would be MASSIVE
                        if(abs(float(num)) < 1.0):
                            discarded_count += 1
                            continue
                            
                        # split up into buckets
                        decimals = len(num.split('.')[1])
                        
                        start_index = d_offset + token_match.start()
                        end_index = d_offset + token_match.end()
                        row = [local_id, shape_idx, start_index, end_index]
                        
                        if(decimals >= 4):
                            # Best candidate: 4+ decimal places (extreme sub-pixel)
                            best_bucket.append(row)
                        elif(decimals == 3):
                            # OK candidate: 3 decimal places (safe)
                            ok_bucket.append(row)
                        elif(decimals == 2):
                            # Next OK candidate: 2 decimal places (borderline)
                            next_ok_bucket.append(row)
                        else:
                            # 1 decimal place is discarded
                            discarded_count += 1
                    else:
                        # Not a control point (it's an anchor point or other command)
                        discarded_count += 1

    # helper function to safely convert our lists into Numpy arrays
    def safe_vstack(lst):
        if(not lst):
            # return an empty 2D array with 4 columns to prevent indexing crashes downstream
            return np.empty((0, 4), dtype=np.int32)
        return np.array(lst, dtype=np.int32)
        
    best = safe_vstack(best_bucket)
    ok = safe_vstack(ok_bucket)
    next_ok = safe_vstack(next_ok_bucket)
    
    total_candidates = len(best) + len(ok) + len(next_ok)

    print("\n--- VECTOR PATH BUCKET SUMMARY ---")
    print(f"Total Floats Evaluated   : {total_floats_evaluated:,}")
    print(f"Untouched / Discarded    : {discarded_count:,}")
    print(f"1. Master BEST (>= 4 dec): {len(best):,}")
    print(f"2. Master OK   (== 3 dec): {len(ok):,}")
    print(f"3. Master NEXT (== 2 dec): {len(next_ok):,}")
    print(f"   --> Total Payload Cap : {total_candidates:,} bits ({total_candidates // 8:,} bytes)")

    # Return a dictionary of the arrays so the Traverser can grab them in order of quality
    return {
        "best": best,
        "ok": ok,
        "next_ok": next_ok
    }
