import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from PIL import Image, ImageTk
import os
from os import listdir
from os.path import isfile, isdir, join
import json
import fnmatch
import sys

from gui.DirSelect import DirSelect
from gui.Logo import Logo
from gui.Reader import Reader


def removeWidget(widget):
    if widget and widget.pack_forget:
        widget.pack_forget()


def initRoot():
    root = tk.Tk()
    root.title("Manga Reader")
    root.attributes('-fullscreen', True)
    root.configure(bg=BACKGROUND_COLOR)

    # Wire up quit action
    root.bind("<Key>", lambda e: quit() if e.keycode == KEY_ESC else None)

    return root


def initReader(root, imageDir, dirSelectWidget):
    reader = Reader(root, imageDir=imageDir, directoryPicker=dirSelectWidget)
    
    return reader



def quit():
    # confirm exit
    result = messagebox.askyesno('Exit', 'Would you like to quit?')

    if not result:
        return

    global root
    root.destroy()


def loadConfig():
    # Assure existence
    if not isfile(CONFIG_FILE):
        open(CONFIG_FILE, 'a').close()
    
    # Attempt to read the json data
    data = {}
    with open(CONFIG_FILE, 'r') as fin:
        data = json.load(fin)

    # Read fields from config if present
    global DEFAULT_DIRECTORY
    global BACKGROUND_COLOR

    if data[CONFIG_DEFAULT_DIRECTORY_FLAG]:
        DEFAULT_DIRECTORY = data[CONFIG_DEFAULT_DIRECTORY_FLAG]
    if data[BACKGROUND_COLOR_FLAG]:
        BACKGROUND_COLOR = data[BACKGROUND_COLOR_FLAG]



KEY_ESC = 3473435
KEY_SHIFT_Q = 81

IMG_PATH = os.path.join('res',)
IMG_FILE = 'logo.jpg'

CONFIG_FILE = 'config.json'

DEFAULT_DIRECTORY = '~'
CONFIG_DEFAULT_DIRECTORY_FLAG = 'defaultDirectory'

BACKGROUND_COLOR = '#5c5c5c'
BACKGROUND_COLOR_FLAG = 'backgroundColor'


loadConfig()
print(f'Config loaded from : {DEFAULT_DIRECTORY}')

# Set up the root
root = initRoot()  

# Create the reader
reader = initReader(root, os.path.join('res', 'demo'), DirSelect)
reader.pack()

# Get rocking!
root.mainloop()



