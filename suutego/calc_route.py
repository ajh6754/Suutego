""" Filename: calc_route.py

    Purpose: The application agnostic solution to calculate a path

    @author Albert Jiro Hynes
"""

from . import hill

def calc_route(layers : list, width : int, height : int, color_space : str):
    """ This function takes info needed to calculate a nice route

        @param layers       - list of dictionaries of bytestrings + positions in image {bytes,x,y,w,h,id}
        @param width        - width of the wider image
        @param height       - height of the wider image
        @param color_space  - could be RGBA or CMYKA or more
        @param password     - if the user desires a password for 
    """
    # calculate pixels/layers we CAN change, and then pixels we shouldn't
    maps = hill.HILL_algo(layers, color_space)

    # obtain traversal seed
    traversal_seed = calc_traversal_seed(layers)

    # return the traversal seed + possible stuff ot do
    return maps, traversal_seed

def calc_traversal_seed(layers : list):
    """ Calculate the PRNG traversal seed (hash) with the width and height of each layer

        @param layers   - list of dictionaries of bytestrings and positions in image
    """
    return None


