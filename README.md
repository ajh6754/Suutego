# Suutego (数テゴ)

Suutego is meant to be a Krita plugin (may branch out to other applications) for message hiding in multi-layer raster image formats.

## Using Suutego

Run `python3 install_deps.py` to install all needed dependencies, Krita does not support packages you may have downloaded to your normal Python environment (such as numpy).

As a note, if you are running Krita on Windows and run the command using WSL, this is likely to fail. Run the command using PowerShell or Command Prompt instead.

## Companion files

To extract Krita layers as PNG for steganography detection testing, companion Python scripts for extracting each paint layer as PNG and each vector layer as SVG were created (located in /layer_extraction). It is not a plugin or part of the plugin, but the scripts were pasted and ran within the Krita Scripter environment.