""" Filename: crypto.py

    Purpose: The application agnostic solution to perform encryption/decryption

    @author Albert Jiro Hynes
"""

import hashlib, struct

def encode(traversal_list : list, message : str, layer_lists : dict, local_id_dict : dict, color_space : str):
    """ Encode the message into the layers

        @param traversal_list - the path we should embed in
        @param message        - the message to embed
        @param layer_lists    - the actual layers we need to modify
        @param local_id_dict  - mapping of local id to Krita layer id
        @param color_space    - our color space
    """
    # prepare an 8 byte header
    sign = b"STEG" 

    # convert the message into bytes/bits
    payload_bytes = message.encode("utf-8")
    header = struct.pack("!4sI", sign, len(payload_bytes))

    bytes_message = header + payload_bytes
    bits = [int(b) for byte in bytes_message for b in f"{byte:08b}"]
    bit_index = 0
    total_bits = len(bits)

    # helpful reference for bits to flip for paint layers
    model_channels = {
        "RGBA" : 4,
        "CMYKA" : 5, 
        "GRAYA" : 2, 
        "YCbCrA" : 4, 
        "XYZA": 4,
        "LABA" : 4 
    }
    total_channels = model_channels[color_space]
    grayscale_magnitude = total_channels - 1

    # each item is a 1D numpy array, [local_id, x, y, channel]
    for action_info in traversal_list:
        krita_layer_id = local_id_dict[action_info[0]]

        # if this is a paint layer
        if(krita_layer_id in layer_lists["paint"].keys()):
            x, y = action_info[1], action_info[2]
            action = action_info[3]
            layer_bytearray = layer_lists["paint"][krita_layer_id]["bytes_array"]
            width = layer_lists["paint"][krita_layer_id]["width"]

            # calculate index in the bytearray we need to flip from
            pixel_start = (y * width + x) * total_channels

            # if the action needs to be done across ALL channels (sans alpha)
            if(action in (318,243)):
                for channel in range(0, grayscale_magnitude):
                    byte_index = pixel_start + channel
                    layer_bytearray[byte_index] = (layer_bytearray[byte_index] & 0xFE) | bits[bit_index]

            # or, we just need to edit one channel
            else:
                channel = action

                # account for if this is actually from the OK bucket
                if(channel >= 10):
                    channel -= 10
                    
                byte_index = pixel_start + channel
                layer_bytearray[byte_index] = (layer_bytearray[byte_index] & 0xFE) | bits[bit_index]

            bit_index += 1

            # replace with our new bytearray
            layer_lists["paint"][krita_layer_id]["bytes_array"] = layer_bytearray
        
        # TODO vector layer

        # TODO filter mask

        # TODO fill layer
        # Exit the main traversal loop if we are done with the message
        if(bit_index >= total_bits):
            break

    return layer_lists


def decode(traversal_list : list, layer_lists : dict, local_id_dict : dict, color_space : str):
    """ Decode the message from the layers

        @param traversal_list - the path we should embed in
        @param layer_lists    - the actual layers we need to modify
        @param local_id_dict  - mapping of local id to Krita layer id
        @param color_space    - our color space
    """

    # helpful reference for bits to flip for paint layers
    model_channels = {
        "RGBA" : 4,
        "CMYKA" : 5, 
        "GRAYA" : 2, 
        "YCbCrA" : 4, 
        "XYZA": 4,
        "LABA" : 4 
    }
    total_channels = model_channels[color_space]
    grayscale_magnitude = total_channels - 1

    # some setup
    extracted_bits = []
    header_bits = 64    # 8 bytes, 4 header + 4 len
    payload_bits_len = None # to be edited later

    header_parsed = False
    message_bytes = None

    # each item is a 1D numpy array, [local_id, x, y, channel]
    for action_info in traversal_list:
        # check if we've gotten the header
        if(not header_parsed and len(extracted_bits) == header_bits):
            header_bytes = bits_to_bytes(extracted_bits)
            sign, payload_len = struct.unpack("!4sI", header_bytes)

            # check the initiator sign
            if(sign != b"STEG"):
                print("No header found, cannot decode message")
                return None

            # if we're golden, get the exact number of bits in the payload
            payload_bits_len = payload_len * 8
            header_parsed = True

            # reset the bits to only be message bits now
            extracted_bits = []

        # check if we're done here
        elif(header_parsed and len(extracted_bits) == payload_bits_len):
            message_bytes = bits_to_bytes(extracted_bits)
            break

        # proceed to analyze 
        krita_layer_id = local_id_dict[action_info[0]]

        # if this is a paint layer
        if(krita_layer_id in layer_lists["paint"].keys()):
            x, y = action_info[1], action_info[2]
            action = action_info[3]
            layer_bytearray = layer_lists["paint"][krita_layer_id]["bytes_array"]
            width = layer_lists["paint"][krita_layer_id]["width"]

            # calculate index in the bytearray we need to flip from
            pixel_start = (y * width + x) * total_channels

            # tells us which channel to read
            channel_to_read = None

            # if the bit was flipped across all channels, we can just do 0
            if(action in (318,243)):
                channel_to_read = 0

            # or, we read from the proper channel
            else:
                channel_to_read = action

            # now, extract the LSB from the affected channel
            byte_index = pixel_start + channel_to_read
            extracted_bit = layer_bytearray[byte_index] & 0x01
            extracted_bits.append(extracted_bit)

        
        # TODO vector layer

        # TODO filter mask

        # TODO fill layer

    return message_bytes.decode("utf-8")


def bits_to_bytes(bits: list) -> bytearray:
    """ Helper to assemble a list of 0s and 1s back into a bytearray 
    """
    byte_array = bytearray()
    for i in range(0, len(bits), 8):
        byte_chunk = bits[i:i + 8]
        # join 8 bits into a single integer byte
        byte_val = int("".join(str(b) for b in byte_chunk), 2)
        byte_array.append(byte_val)
    return byte_array


def calc_traversal_seed(layer_lists : dict):
    """ Calculate the PRNG traversal seed (hash)

        At minimum this uses the starting x/y, width/height, and id of each
        paint layer, but other attrs may also be considered.

        @param layer_lists - 
        @param seed_plus   - list of additional attrs to be used in seed generation
    """
    seed_components = []

    # want to be ultra deterministic, we use "paint" first
    if("paint" in layer_lists.keys()):
        for layer_id in layer_lists["paint"].keys():
            layer = layer_lists["paint"][layer_id]
            seed_components.append(f"node {layer_id}:{layer["width"]}x{layer["height"]}:{layer["x"]},{layer["y"]}")

    # TODO vector

    # TODO maybe fill/filter mask/layer

    # create deterministic sha-256 hash
    raw_key = "|".join(seed_components).encode('utf-8')
    hash_digest = hashlib.sha256(raw_key).digest()

    # create seed
    seed = int.from_bytes(hash_digest[:8], byteorder='big')

    return seed