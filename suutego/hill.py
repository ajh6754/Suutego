""" 
Filename: hill.py

This runs a modified HILL strategy.

first identify all possible pixels by running modified HILL on ALL pixels
    modified HILL will ignore all LSB of every color channel, which works out for encoder/decoder
    modified HILL will run on every channel independently then pick the best (least) cost channel
        ALWAYS ignore the alpha (last)

then use the seeded PRNG to iterate through those candidates semi-randomly

future work: implementing something like GINA-HILL that concerns all 3 channels
- there is an added complexity with layered images so that might also require hefty research

@author Albert Jiro Hynes
"""

import scipy.signal
import numpy as np

# HILL setup

# H filter is a 3x3 KB filter
H = np.array([                                                             
    [-1, 2, -1],                                                             
    [ 2,-4,  2],                                                             
    [-1, 2, -1]                                                              
])       

# L_1 filter is a 3x3 filter
L_1 = [
    [1/9, 1/9, 1/9],
    [1/9, 1/9, 1/9],
    [1/9, 1/9, 1/9]
]

# L_2 filter is a 15x15 filter
L_2 = []
for i in range(0,15):
    row = [1/255] * 15
    L_2.append(row)


# minimum variance to be considered for HILL
MIN_VARIANCE = 1.0


# did this so we had less computations to do
TEN_POWER_ADD = 10**(-10)

def HILL_cost(layer_matrix):                                                                                        
    """ HILL cost function
    """
    R1 = scipy.signal.convolve2d(layer_matrix, H, mode='same', boundary='symm')
    W1 = scipy.signal.convolve2d(np.abs(R1), L_1, mode='same', boundary='symm')
    rho = 1./(W1+TEN_POWER_ADD)
    cost = scipy.signal.convolve2d(rho, L_2, mode='same', boundary='symm')

    # now that we have costs, filter out the pure black/transparent/empty pixels
    cost[layer_matrix == 0] = np.inf

    return cost 


def HILL_algo(layers, color_model):
    """ This function deals with identifying what pixels in each layer to change
    
        @param layers       - list of dictionaries of bytestrings and positions in image
        @param color_model  - color model we're working with
    """
    # dictionaries to hold layers + which pixels (and channel) to flip 
    # ex. {"layer_id" : map}
    maps = {}

    # information variables
    total_best_sum = 0
    total_ok_sum = 0

    for layer in layers:
        # get the layer info
        bytes_array = layer["bytes_array"]
        width = layer["width"]
        height = layer["height"]

        # split the image into its channels
        channel_arrays = convert_layer_to_2d_arr(bytes_array, width, height, color_model)

        # determine if the layer is acceptable, feed into HILL if so
        HILL_cost_matrix = {}
        for key in channel_arrays.keys():
            array_variance = np.var(channel_arrays[key])
            
            # if good, feed channel into HILL
            if(array_variance >= MIN_VARIANCE):
                HILL_cost_matrix[key] = HILL_cost(channel_arrays[key])

        # if the whole layer fails then leave
        if(len(HILL_cost_matrix.keys()) == 0):
            continue

        # get the aggregate min cost across all color channels
        cost_channels = list(HILL_cost_matrix.values())
        agg_cost_map = np.sqrt(np.sum([C**2 for C in cost_channels], axis=0))
        valid_costs = agg_cost_map[agg_cost_map < np.inf]

        # if the whole layer fails then leave
        if(len(valid_costs) == 0):
            continue

        # else we declare the minimum cost across all channels
        c_min = np.min(valid_costs)

        # after determining the min, declare bounds

        # Strategy: Best candidates have cost =< c_min * 1.5 and cost > 0
        # Ok candidates have cost < c_min * 3 and cost > 1.5... or something like that
        # literally anything beyond that is bad

        best_cost_upper_bound = c_min * 1.5
        ok_cost_upper_bound = c_min * 3

        # now get the cost stack across all channels, obtain mins per channel
        cost_stack = np.stack(list(HILL_cost_matrix.values()), axis=-1)
        min_channel_map = np.argmin(cost_stack, axis=-1)

        # stack the channels together to just get the MSB stack 
        channel_msb_stack = np.stack(list(channel_arrays.values()), axis=-1)

        # create nice masks for speed/simplicity
        best_mask = (agg_cost_map <= best_cost_upper_bound) & (agg_cost_map < np.inf)
        ok_mask = (agg_cost_map > best_cost_upper_bound) & (agg_cost_map <= ok_cost_upper_bound) & (agg_cost_map < np.inf)

        # perform a grayscale check on most significant 7 bits, to act as a mask
        is_grayscale = np.all(channel_msb_stack == channel_msb_stack[..., :1], axis=-1)

        # based on this construct a final target action 2d map, -1 = don't touch
        target_action_map = np.full(agg_cost_map.shape, -1, dtype=int)

        ###
        ### BEST BUCKET
        ###

        # determine best color based on minimum channel index (0, 1, 2...)
        # ignoring grayscale
        best_color = best_mask & (~is_grayscale)
        target_action_map[best_color] = min_channel_map[best_color]
        
        # for grayscale, assign code 318
        best_gray = best_mask & is_grayscale
        target_action_map[best_gray] = 318

        ###
        ### OK BUCKET
        ###

        # determine best color based on minimum channel index (0, 1, 2...)
        # ignoring grayscale
        ok_color = ok_mask & (~is_grayscale)
        target_action_map[ok_color] = min_channel_map[ok_color]
        
        # for grayscale, assign code 243
        ok_gray = ok_mask & is_grayscale
        target_action_map[ok_gray] = 243

        ###
        ### ADD TO CANDIDATE LIST
        ###
        maps[layer["id"]] = target_action_map


        ###
        ### SUMMARY
        ###

        total_pixels = target_action_map.size 
        # 1. Count discarded / untouched pixels
        untouched_count = np.sum(target_action_map == -1)

        # 2. Count Best Candidates (Color channels 0, 1, 2... and Grayscale 99)
        best_color_count = np.sum((target_action_map >= 0) & (target_action_map < 10))
        best_gray_count  = np.sum(target_action_map == 318)
        total_best       = best_color_count + best_gray_count

        # 3. Count OK Candidates (Color channels 10, 11, 12... and Grayscale 98)
        ok_color_count   = np.sum((target_action_map >= 10) & (target_action_map <= 13))
        ok_gray_count    = np.sum(target_action_map == 243)
        total_ok         = ok_color_count + ok_gray_count

        # 4. Total available payload capacity (in bits/pixels)
        total_candidates = total_best + total_ok

        print("--- HILL TARGET ACTION MAP SUMMARY ---")
        print(f"Layer id            : {layer["id"]}")
        print(f"Total Canvas Pixels : {total_pixels:,}")
        print(f"Untouched / Discard : {untouched_count:,} ({untouched_count/total_pixels:.2%})")
        print(f"Best Color Pixels   : {best_color_count:,}")
        print(f"Best Grayscale      : {best_gray_count:,}")
        print(f"TOTAL BEST POOL     : {total_best:,} ({total_best/total_pixels:.2%})")
        print(f"OK Color Pixels     : {ok_color_count:,}")
        print(f"OK Grayscale        : {ok_gray_count:,}")
        print(f"TOTAL OK POOL       : {total_ok:,} ({total_ok/total_pixels:.2%})")
        print(f"Total Embed Capacity: {total_candidates:,} pixels ({total_candidates/total_pixels:.2%})")

        total_best_sum += total_best
        total_ok_sum += total_ok

    total_sum = total_best_sum + total_ok_sum

    print()
    print("--- HILL TOTAL SUMMARY ---")
    print(f"Total best pixels:       : {total_best_sum}")
    print(f"Total ok pixels:         : {total_ok_sum}")
    print(f"Total pixels:            : {total_sum}")

    return maps, total_best_sum, total_ok_sum

def convert_layer_to_2d_arr(bytes_array, width, height, color_model):
    """ function to convert the bytearray into 2D arrays (1 for each channel, ignore alpha)

        Each array is not a perfect copy- LSB is removed so a decoder gets the same result
    """
    # map for proper orders
    model_channel_map = {
        "RGBA": [0, 1, 2], 
        "CMYKA": [0, 1, 2, 3],
        "GRAYA": [0],
        "LABA": [0, 1, 2], 
        "XYZA": [0, 1, 2], 
        "YCbCrA": [0, 1, 2]
    }

    model_channels = {
        "RGBA" : 4,
        "CMYKA" : 5, 
        "GRAYA" : 2, 
        "YCbCrA" : 4, 
        "XYZA": 4,
        "LABA" : 4 
    }

    num_channels = model_channels[color_model]

    # convert raw bytearray to a numpy array
    flat_arr = np.frombuffer(bytes_array, dtype=np.uint8)

    # reshape into 3D structure: (Height, Width, Channels)
    img_3d = flat_arr.reshape((height, width, num_channels))
    channel_names = model_channel_map[color_model]
    num_color_channels = len(channel_names)

    color_channels = {}
    for i in range(0,num_color_channels):
        color_channels[channel_names[i]] = np.ascontiguousarray(
            img_3d[:, :, i] & 0xFE
        )

    return color_channels

