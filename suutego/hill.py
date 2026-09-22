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


def HILL_cost(layer_matrix):                                                                                        
    """ HILL cost function
    """
    # 

    # following is ripped from https://github.com/daniellerch/stegolab/blob/master/HILL/HILL.py
    R1 = scipy.signal.convolve2d(layer_matrix, H, mode='same', boundary='symm')
    W1 = scipy.signal.convolve2d(np.abs(R1), L_1, mode='same', boundary='symm')
    rho = 1./(W1+10**(-10))
    cost = scipy.signal.convolve2d(rho, L_2, mode='same', boundary='symm')
    return cost 

# what is the HILL Strategy?

# first identify all possible pixels by running modified hill on ALL pixels
    # modified HILL will ignore all LSB of every color channel, which works out for encoder/decoder
    # modified HILL will run on every channel independently then pick the best (least) cost channel
        # ALWAYS ignore the alpha (last)

# then use the seeded PRNG to iterate through those candidates semi-randomly


def HILL_algo(layers, color_model):
    """ This function deals with identifying what pixels in each layer to change (in order)
    
        @param layers       - list of dictionaries of bytestrings and positions in image
        @param num_channels - number of color channels in image
    """
    # for sake of simplicity, compromising with only B in RGB and only Y in CMYK
    
    # OR, doing all 3 (still ignoring grayscale), jumping around all of those

    # for human detection, changes to blue are most imperceptible
    # if grayscale, then flip all relevant bits
    # this reduces the number of bits, but that's fine- not getting caught is more important
    # future work: implementing something like GINA-HILL

    # dictionary to hold layers + which pixels (and channel) to flip 
    # ex. {"layer_id" : [(x,y,channel_index)]}
    alter_candidates = {}

    for layer in layers:
        # get the layer info
        bytes_array = layer["bytes_array"]
        width = layer["width"]
        height = layer["height"]

        # split the image into its channels
        channel_arrays = convert_layer_to_2d_arr(bytes_array, width, height, color_model)

        # feed each channel into HILL
        HILL_cost_matrix = {}
        for key in channel_arrays.keys():
            HILL_cost_matrix[key] = HILL_cost(channel_arrays[key])
            print(HILL_cost_matrix[key])

        # now, identify all coordinate pairs and channel to alter
        


    # for any grayscale (all color values are equal and in (0,255)), flip every LSB
    return None

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