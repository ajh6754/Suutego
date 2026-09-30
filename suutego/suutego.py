"""
Filename:   suutego.py

Purpose:    To act as the Suutego initial load (grab all layers/bitmaps) before
            encoding or decoding messages. Any print statements can be
            commented out if desired.

@author:    Albert Jiro Hynes
"""

from krita import Krita, Extension
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, 
    QTextEdit, QLineEdit, QPushButton, QGroupBox, QMessageBox, QWidget
)
from PyQt5.QtCore import Qt
from . import calc_route, crypto

"""
TODO (in order)

- encoding, decoding
    - at present just normal image layers
        - HILL improvement - try to prioritize 10-12k or below per layer
    - other layer types later on

- use of other layer types (really upgrades this to a "can't just do this on PNG" level)
    - Vector layer (comic strip shapes, logo, noncomlpex art, calliigraphy)
        - approach: Dicrete Wavelet Transform?
        - still using randomized traversal + encryption
    - Fill layer?
        - 
    - filter mask?

"""

###
### CLASSES
###

class SuutegoDialog(QDialog):
    def __init__(self, parent, paint_layers, vector_layers, local_id_layer_mappings, doc_width, doc_height, color_model):
        super().__init__(parent)
        self.setWindowTitle("Suutego - Multi-Layer Steganography Tool")
        self.resize(580, 550)
        
        # krita file data
        self.paint_layers = paint_layers
        self.vector_layers = vector_layers
        self.local_id_layer_mappings = local_id_layer_mappings
        self.doc_width = doc_width
        self.doc_height = doc_height
        self.color_model = color_model

        # state stored after calculating route
        self.seed = None
        self.layers_analyzed = False
        self.paint_layer_buckets = None
        self.num_paint_best = 0
        self.num_paint_next_best = 0
        self.num_paint_ok = 0
        self.paint_max_chars = 0
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # first verify that the user wants to do this
        analysis_group = QGroupBox("Perform modified HILL Route Analysis")
        analysis_layout = QVBoxLayout()
        
        intro_lbl = QLabel(
            "Before embedding or decoding, run the modified HILL algorithm to "
            "identify usable target pixels across all active layers."
        )
        intro_lbl.setWordWrap(True)
        analysis_layout.addWidget(intro_lbl)

        btn_layout = QHBoxLayout()
        self.btn_run_hill = QPushButton("Analyze Active File")
        self.btn_run_hill.clicked.connect(self.run_hill_analysis)
        btn_layout.addWidget(self.btn_run_hill)
        analysis_layout.addLayout(btn_layout)

        # seeing capacity
        self.stats_label = QLabel("Status: Route analysis pending...")
        self.stats_label.setTextFormat(Qt.RichText)
        analysis_layout.addWidget(self.stats_label)

        analysis_group.setLayout(analysis_layout)
        main_layout.addWidget(analysis_group)

        # now create tabs for encoding and decoding
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_encode_tab(), "Encode")
        self.tabs.addTab(self.create_decode_tab(), "Decode")
        self.tabs.setEnabled(False)  # Require verification first
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def run_hill_analysis(self):
        """ Runs calc_paint_layers after explicit user confirmation 
        """
        reply = QMessageBox.question(
            self, 
            "Confirm Route Calculation",
            "Perform analysis on the current image layers now?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.Yes
        )

        if(reply == QMessageBox.Yes):
            # paint layer calculation
            self.paint_layer_buckets = calc_route.calc_paint_layers(
                self.paint_layers, self.local_id_layer_mappings, self.color_model
            )
            self.layers_analyzed = True

            # get stats
            self.num_paint_best = len(self.paint_layer_buckets["best"])
            self.num_paint_next_best = len(self.paint_layer_buckets["next_best"])
            self.num_paint_ok = len(self.paint_layer_buckets["ok"]) + len(self.paint_layer_buckets["next_ok"])
            total_avail = self.num_paint_best + self.num_paint_next_best + self.num_paint_ok

            # update the UI for stats on how much we can add
            # the first 4 bytes will be a signature, next 4 is length of message, then payload

            total_avail = total_avail - 8
            approx_best_bytes = (self.num_paint_best // 8) - 8
            approx_next_best_bytes = ((self.num_paint_best + self.num_paint_next_best) // 8) - 8
            approx_bytes = (total_avail // 8) - 8
            self.paint_max_chars = approx_bytes

            # if there literally isn't enough for a payload then stop here
            if(total_avail <= 0):
                self.stats_label.setText(
                    f"<b>This file is not suitable for a message using Suutego.</b><br>"
                    f"Please pick another file or draw."
                )
            else:
                stats_string = f"<b>Best Pixels:</b> {self.num_paint_best:,} | <b>Total Available:</b> {total_avail:,}<br>" + \
                        f"<b>Est. Best Only Max Capacity:</b> ~{approx_best_bytes:,} characters<br>" + \
                        f"<b>Est. Next Best Max Capacity:</b> ~{approx_next_best_bytes:,} characters<br>" + \
                        f"<b>Est. Total Payload Capacity:</b> ~{approx_bytes:,} characters"

                if(approx_best_bytes < 10):
                    stats_string += f"<br><br>Since there are very little good candidates for stego, " + \
                                    "you should<br>probably use a different file or draw."

                self.stats_label.setText(stats_string)

                # NOW unlock encode/decode
                self.tabs.setEnabled(True)

            # if desired this can be re-analyzed although there is little purpose
            self.btn_run_hill.setText("Re-analyze Image")

    def create_encode_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Message to Embed:"))
        self.encode_text = QTextEdit()
        self.encode_text.setPlaceholderText("Enter secret message here...")
        layout.addWidget(self.encode_text)

        # TODO consider password
        # layout.addWidget(QLabel("Passphrase (Optional):"))
        # self.encode_key = QLineEdit()
        # self.encode_key.setEchoMode(QLineEdit.Password)
        # layout.addWidget(self.encode_key)

        btn_encode = QPushButton("Encode Payload into Image")
        btn_encode.clicked.connect(self.on_encode_click)
        layout.addWidget(btn_encode)

        widget.setLayout(layout)
        return widget

    def create_decode_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # TODO consider passwords
        # layout.addWidget(QLabel("Passphrase (If encrypted):"))
        # self.decode_key = QLineEdit()
        # self.decode_key.setEchoMode(QLineEdit.Password)
        # layout.addWidget(self.decode_key)

        btn_decode = QPushButton("Scan & Extract Message")
        btn_decode.clicked.connect(self.on_decode_click)
        layout.addWidget(btn_decode)

        layout.addWidget(QLabel("Extracted Payload:"))
        self.decode_text = QTextEdit()
        self.decode_text.setReadOnly(True)
        layout.addWidget(self.decode_text)

        widget.setLayout(layout)
        return widget

    def on_encode_click(self):
        message = self.encode_text.toPlainText()

        if not message:
            QMessageBox.warning(self, "Warning", "Please enter a message to encode.")
            return

        # encode
        # success = crypto.encode(message, self.maps, self.seed)
        
        QMessageBox.information(self, "Success", "Message successfully embedded into active layers!")
        self.accept()

    def on_decode_click(self):
        # decode
        # extracted_msg = crypto.decode(self.maps, self.seed)
        extracted_msg = "Sample decoded message from stego pixels."

        if extracted_msg:
            self.decode_text.setPlainText(extracted_msg)
            QMessageBox.information(self, "Found", "Message successfully decoded!")
        else:
            QMessageBox.warning(self, "Failed", "No hidden message found or incorrect passphrase.")

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
        paint_layers, vector_layers = self.obtain_all_layers(top_level_nodes)

        # color model (RGBA, CMYKA, GRAYA, YCbCrA, LABA, XYZA)
        color_model = doc.colorModel()

        # get bounds
        doc_bounds = doc.bounds()
        doc_width = doc_bounds.width()
        doc_height = doc_bounds.height()

        # create local id to Krita layer ID mappings (speedup later)
        index = 0
        local_id_layer_mappings = {}
        for layer_list in [paint_layers, vector_layers]:
            for layer in layer_list:
                local_id_layer_mappings[index] = layer["id"]
                local_id_layer_mappings[layer["id"]] = index
                index += 1

        # Launch Custom UI Prompt
        main_window = app.activeWindow().qwindow()
        dialog = SuutegoDialog(main_window, paint_layers, vector_layers, local_id_layer_mappings, doc_width, doc_height, color_model)
        dialog.exec_()

    def obtain_all_layers(self, nodes):
        """ Recursive function to grab all relevant layers, convert to bitmap

            TODO separate logic for non color/paint layers:
                - transparency masks?
                - alpha mask? prob not
                - vector layers
                - filter layers
        """
        paint_layers = []
        vector_layers = []

        for node in nodes:
            # get the children, if there are none then we're done
            node_children = node.childNodes()

            if(len(node_children) > 0):
                new_paint_layers, new_vector_layers = self.obtain_all_layers(node_children)
                paint_layers.extend(new_paint_layers)
                vector_layers.extend(new_vector_layers)
            
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
                paint_layers.append({"bytes_array" : bytes_array, "x" : starting_x, "y" : starting_y, "width" : width, "height" : height, "id" : node.uniqueId()})
            
            elif(node.type() == "vectorlayer"):
                # get all vector shapes inside this layer, if we have none skip 
                shapes = node.shapes()

                if(len(shapes) == 0):
                    print(f"Layer '{node.name()}' is empty, ignoring...")
                    continue

                # get an ordered list of shapes turned to SVG
                svg_list = []

                for shape in shapes:
                    svg_list.append(shape.toSvg())

                # grab the SVG representing this vector layer
                vector_layers.append({"svg_list" : svg_list, "id" : node.uniqueId()})

            elif(node.type() == "filllayer"):
                print("TODO")

            elif(node.type() == "filtermask"):
                print("TODO")

        return paint_layers, vector_layers

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
