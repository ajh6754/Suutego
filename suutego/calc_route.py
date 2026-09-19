""" Filename: calc_route.py

    Purpose: The application agnostic solution to calculate a path

    @author Albert Jiro Hynes
"""

def calc_route(layers : list, width : int, height : int, color_space : str):
    """ This function takes info needed to calculate a nice route

        @param layers       - list of dictionaries of bytestrings + positions in image {bytes,x,y}
        @param width        - width of the wider image
        @param height       - height of the wider image
        @param color_space  - could be RGBA or CMYKA or more
        @param password     - if the user desires a password for 
    """
    # perform hilbert algo- remove any unnecessary bits
    route = hilbert_algo(layers)

    # obtain traversal seed
    traversal_seed = calc_traversal_seed(layers)

    # return the traversal seed + possible stuff ot do
    return route, traversal_seed

def calc_traversal_seed(layers : list):
    """ Calculate the PRNG traversal seed (hash) with the width and height of each layer

        @param layers   - list of dictionaries of bytestrings and positions in image
    """
    return None

def hilbert_algo(layers):
    """ This function deals with the Hilbert Space-Filling Curve part of this
    
        @param layers   - list of dictionaries of bytestrings and positions in image
    """
    return None


