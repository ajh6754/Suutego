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


def HILL_algo(layers, color_model, test=None):
    """ This function deals with identifying what pixels in each layer to change
    
        @param layers       - list of dictionaries of bytestrings and positions in image
        @param color_model  - color model we're working with
        @param test         - var to indicate visual test rather than actual stego
    """
    # dictionaries to hold layers + which pixels (and channel) to flip 
    # ex. {"layer_id" : map}
    maps = {}

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
        target_action_map[ok_color] = min_channel_map[best_color]
        
        # for grayscale, assign code 243
        ok_gray = ok_mask & is_grayscale
        target_action_map[ok_gray] = 243

        ###
        ### ADD TO CANDIDATE LIST
        ###
        maps[layer["id"]] = target_action_map

    return maps

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

    
### TODO
"""
- converting to 2d array function (done)
- no LSB hill algorithm on all 3-4 channels (ignore alpha)
    - select best channel
- return all pixels we can flip
"""

"""
"""
    

# def old_algo(layers, num_channels):
    # establish channels we can do
    # channel_list = []
    # for i in range(0,num_channels-1):
    #     channel_list.append[i]

    # for layer in layers:
    #     # do a simple 3x3 spatial entropy approach for now and see how it goes...

    #     # get the layer info
    #     bytes_array = layer["bytes_array"]
    #     width = layer["width"] - 1
    #     height = layer["height"] - 1

    #     # for all x,y coords in the layer, determine if it's worth using
    #     for y in range(1, height):
    #         for x in range(1, width):
    #             index = ((y * width) + x) * num_channels
    #             pixel_color_channels = []

    #             # extract channel values
    #             for i in range(0,len(channel_list)):
    #                 pixel_color_channels.append(bytes_array[index + i])

    #             # check if it's grayscale or 0/255
    #             is_uniform = len(set(pixel_color_channels)) == 1

    #             # first check if this is a 0,0,0 or 255,255,255- ignore if so
    #             if(is_uniform and pixel_color_channels[0] % 255 == 0):
    #                 continue

    #             # now see what we should flip- if grayscale then do all


    # for any grayscale (all color values are equal and in (0,255)), flip every LSB

    # return type: {layer_id : [(x,y,{0 || 1 || 2 || 3})], ...]}

    # return None

# def get_pixel_channel_val(data: bytearray, width: int, x: int, y: int, num_channels: int, channel_idx: int):
#     """ returns byte value at (x, y) for a specific channel
#     """
#     return data[(y * width + x) * num_channels + channel_idx]

# def calculate_local_entropy(data: bytearray, width: int, height: int, x: int, y: int, num_channels: int, channel_idx: int, radius: int = 1):
#     """ calculates Shannon entropy in a local (2*radius + 1) neighborhood for a specific channel
#     """
#     neighborhood_vals = []
    
#     # Extract values from the surrounding bounding box
#     for ny in range(max(0, y - radius), min(height, y + radius + 1)):
#         for nx in range(max(0, x - radius), min(width, x + radius + 1)):
#             val = get_pixel_channel_val(data, width, nx, ny, num_channels, channel_idx)
#             neighborhood_vals.append(val)
            
#     # Calculate Shannon Entropy: H = -sum(P(x) * log2(P(x)))
#     total_pixels = len(neighborhood_vals)
#     counts = Counter(neighborhood_vals)
    
#     entropy = 0.0
#     for count in counts.values():
#         p = count / total_pixels
#         entropy -= p * math.log2(p)
        
#     return entropy