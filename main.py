import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from PIL import Image, ImageTk
import os
import sys



class Logo(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        try:
            self.imagePath = kwargs.pop('path', None)
            load = Image.open(self.imagePath)
            load.thumbnail((250, 250), Image.ANTIALIAS)
            self.image = ImageTk.PhotoImage(load)
        except Exception as e:
            print(str(e))
            print('Please supply an image file')
            exit()
        
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.parent = parent

        self.imageLabel = tk.Label(self.parent, image=self.image)
        self.imageLabel.image = self.image
        self.imageLabel.pack()


class DirSelect(tk.Frame):


    def __init__(self, parent, *args, **kwargs):
        try:
            self.onDirectorySelect = kwargs.pop('onDirectorySelect', None)
        except:
            print('Please supply a callback for directory selection!')
            exit()
        
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.parent = parent
        

        sizex = 800
        sizey = 600
        self.root = tk.Frame(self.parent, width=sizex, height=sizey, padx=10, pady=10)

        # Select Button
        self.selectButton = tk.Button(self.root, command=self.openDirectorySelect, text='Choose Manga Directory', fg='red')
        self.selectButton.pack()

        # Directory Label
        self.directoryLabel = tk.Label(self.root, text='[No Directory Selected]')
        self.directoryLabel.pack()

        # Start Reading Button
        self.readButton = tk.Button(self.root, command=self.startReading, text='Start Reading', state='disabled')
        self.readButton.pack()


        self.root.pack()

    def openDirectorySelect(self):
        self.mangaDir = filedialog.askdirectory(initialdir = "~",title = "Select Manga Folder")

        if (self._pathIsValid(self.mangaDir)):
            # Update our label and the button state
            self.directoryLabel['text'] = self.mangaDir
            self.readButton['state'] = 'active'

    def startReading(self):

        if (self.mangaDir and os.path.isdir(self.mangaDir) and os.path.exists(self.mangaDir)):
            print('Good to start reading from: ' + str(self.mangaDir))
            print('executing read callback!')
            self.onDirectorySelect()
        else:
            messagebox.showerror("Error", "Please select a manga directory")


    def _pathIsValid(self, path):
        return path and os.path.isdir(path) and os.path.exists(path)



def onSelectCallback():
    print('this is where we\'d swap some stuff around')



KEY_SHIFT_Q = 81
KEY_LEFT = 8124162
KEY_RIGHT = 8189699
KEY_UP = 8320768
KEY_DOWN = 8255233

IMG_PATH = os.path.join('res',)
IMG_FILE = 'logo.jpg'

master = tk.Tk()
master.title("Manga Reader")
master.attributes('-fullscreen', True)  




# Wire up the select section guy
select = DirSelect(master, onDirectorySelect=onSelectCallback)
select.pack()

# Add the logo :)
logo = Logo(master, path=os.path.join(IMG_PATH, IMG_FILE))
logo.pack()

master.mainloop()







print('Running...')


