"""
Filename:   suutego.py

Purpose:    To act as the Suutego initial load (grab all layers/bitmaps) before
            encoding or decoding messages. Any print statements can be
            commented out if desired.

@author:    Albert Jiro Hynes
"""

from krita import Krita, Extension
from PyQt5.QtWidgets import QMessageBox
from . import calc_route, crypto

###
### CLASSES
###

class SuutegoExtension(Extension):

    def __init__(self, parent):
        # This is initialising the parent, always important when subclassing.
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        suutego_action = window.createAction("suutego", "Suutego", "tools/scripts")
        suutego_action.triggered.connect(self.initialize)

    def initialize(self):
        """ Function to start suutego
        """
        app = Krita.instance()
        window = app.activeWindow()
        doc = None

        # only proceed if we have an active document
        if(window is not None):
            view = window.activeView()

            if(view is not None):
                doc = view.document()

        # if doc is none, do nothing
        if(doc is None):
            self.ran_without_doc()
            return

        # obtain all top level nodes, need to check for groups of layers
        top_level_nodes = doc.topLevelNodes()

        # list of layers to determine path, encode, and decode
        layers = self.obtain_all_layers(top_level_nodes)

        # color model (CMYKA, RGBA, GRAYA, YCbCrA, LABA, XYZA)
        color_model = doc.colorModel()

        # get bounds
        doc_bounds = doc.bounds()
        doc_width = doc_bounds.width()
        doc_height = doc_bounds.height()

        # pass layers into calc_route.py, layers are in reverse order of precedence
        route, seed = calc_route.calc_route(layers, doc_width, doc_height, color_model)

        # EDIT LATER: to become the Suutego prompt
        main_window = Krita.instance().activeWindow().qwindow()
        msg_box = QMessageBox(main_window)
        msg_box.setWindowTitle("Suutego")
        msg_box.setText("Welcome to Suutego.")
        # consider updates of "message present" or somethin here
        msg_box.setInformativeText("You can display status updates or warnings here.")
        # maybe an icon?
        msg_box.setIcon(QMessageBox.Information)
        # need buttons like Encode, Decode... text box to encode, etc.
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()

    def obtain_all_layers(self, nodes):
        """ Recursive function to grab all relevant layers, convert to bitmap
        """
        layers = []

        for node in nodes:
            # get the children, if there are none then we're done
            node_children = node.childNodes()

            if(len(node_children) > 0):
                layers.extend(self.obtain_all_layers(node_children))
            elif(node.type() == "paintlayer"):
                # get pixel data
                bounds = node.bounds()
                width = bounds.width()
                height = bounds.height()

                # check for an empty layer
                if(width == 0 or height == 0):
                    print(f"Layer '{node.name()}' is empty, ignoring...")
                    continue

                starting_x, starting_y = bounds.x(), bounds.y()

                # grab pixel data, convert to bytearray for mutability
                pixel_data = node.pixelData(starting_x, starting_y, bounds.width(), bounds.height())
                bytes_array = bytearray(pixel_data)

                # now append the raw bitmap
                layers.append({"bytes_array" : bytes_array, "x" : starting_x, "y" : starting_y})

        return layers

    def ran_without_doc(self):
        """ Flash a warning if a user attempts to run without having an active document open
        """
        main_window = Krita.instance().activeWindow().qwindow()
        msg_box = QMessageBox(main_window)
        msg_box.setWindowTitle("Suutego Error")
        msg_box.setText("Error: No document detected")
        msg_box.setInformativeText("Please open a document before running Suutego.")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()

###
### LOAD THE PLUGIN
###

Krita.instance().addExtension(SuutegoExtension(Krita.instance()))
