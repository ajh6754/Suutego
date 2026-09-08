"""
Filename:   suutego.py

Purpose:    To act as the Suutego initial load (grab all layers/bitmaps) before
            encoding or decoding messages. 

@author:    Albert Jiro Hynes
"""

from krita import Krita, Extension
from PyQt5.QtWidgets import QMessageBox

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
        layers = doc.topLevelNodes()

        # EDIT LATER: to become the Suutego prompt
        main_window = Krita.instance().activeWindow().qwindow()
        msg_box = QMessageBox(main_window)
        msg_box.setWindowTitle("Plugin Notification")
        msg_box.setText("Hello! This is a simple Krita popup.")
        msg_box.setInformativeText("You can display status updates or warnings here.")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()


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
