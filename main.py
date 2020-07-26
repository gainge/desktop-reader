import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from PIL import Image, ImageTk
import os
from os import listdir
from os.path import isfile, join
import fnmatch
import sys



class Reader(tk.Frame):
    IMAGE_HEIGHT_SCALE = 1.8
    SCROLL_SPEED = 10

    def __init__(self, parent, *args, **kwargs):
        try:
            self.imageDir = kwargs.pop('imageDir', None)
        except Exception as e:
            print(str(e))
            exit()

        tk.Frame.__init__(self, parent, *args, **kwargs)

        # get some routine initialization out of the way
        self.parent = parent
        self.parentHeight = parent.winfo_screenheight()
        self.imageHeight = self.IMAGE_HEIGHT_SCALE * self.parentHeight
        self.imageIndex = 0

        self.canvas = tk.Canvas(self.parent)
        # scroll_y = tk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        frame = tk.Frame(self.canvas)

        # See if we can read some images from here, eh?
        mangaFiles = [f for f in listdir(self.imageDir) if isfile(join(self.imageDir, f)) and (fnmatch.fnmatch(f, '*.png') or fnmatch.fnmatch(f, '*.jpg'))]
        mangaFiles.sort()

        self.mangaFiles = mangaFiles
        self.images = [None] * len(mangaFiles)
        print(mangaFiles)

        self.image = self._loadImage()

        self.pagesLabel = tk.Label(frame, text=self._createPagesText())
        self.pagesLabel.pack()


        self.canvas.create_window(0, 0, anchor='nw', window=frame)
        self.canvas.bind_all("<MouseWheel>", lambda event: self.canvas.move(self.image, 0, event.delta * self.SCROLL_SPEED))
        self.canvas.bind_all("<Key>", self.keyPress)

        self.canvas.update_idletasks()

        self.canvas.pack(fill='both', expand=True, side='left')

    def keyPress(self, e):
        if e.keycode == KEY_LEFT:
            self.nextImage()
        elif e.keycode == KEY_RIGHT:
            self.prevImage()

    
    def nextImage(self):
        if self.imageIndex >= len(self.mangaFiles):
            return
        
        self.changePage(self.imageIndex + 1)


    def prevImage(self):
        if self.imageIndex <= 0:
            return
        
        self.changePage(self.imageIndex - 1)

    def reloadImage(self):
        self.changePage(self.imageIndex)

    def changePage(self, newIndex):
        # Delete the current image
        if (self.image): self.canvas.delete(self.image)

        # Load the new index
        self.imageIndex = newIndex
        self.image = self._loadImage(newIndex) # display new image and delete
        self.pagesLabel['text'] = self._createPagesText()

    
    def _loadImage(self, index=0):
        image = self._getMangaImage(index)
        width = self.parent.winfo_width()
        return self.canvas.create_image(width/2, 0, image=image, anchor='n')

    
    def _getMangaImage(self, index):
        if not self.images[index]:
            # Load the image, it's not cached
            imageName = self.mangaFiles[index]
            load = Image.open(join(self.imageDir, imageName))
            load.thumbnail((self.imageHeight, self.imageHeight), Image.ANTIALIAS)
            self.images[index] = ImageTk.PhotoImage(load)
        
        return self.images[index]


    def _createPagesText(self):
        return f"{self.imageIndex + 1} / {len(self.mangaFiles)}"


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



def initSelectGUI(root):
    # Wire up the select section guy
    select = DirSelect(root, onDirectorySelect=onSelectCallback)
    select.pack()

    # Add the logo :)
    logo = Logo(root, path=os.path.join(IMG_PATH, IMG_FILE))
    logo.pack()


def initReader(root, imageDir):
    reader = Reader(root, imageDir=imageDir)
    reader.pack()

KEY_SHIFT_Q = 81
KEY_LEFT = 8124162
KEY_RIGHT = 8189699
KEY_UP = 8320768
KEY_DOWN = 8255233

IMG_PATH = os.path.join('res',)
IMG_FILE = 'logo.jpg'

# Set up the root
root = tk.Tk()
root.title("Manga Reader")
root.attributes('-fullscreen', True)  

# Add the initial selection widgets
# initSelectGUI(root)
initReader(root, os.path.join('res', 'demo'))


# Get rocking!
root.mainloop()







print('Running...')


