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



class Reader(tk.Frame):
    IMAGE_HEIGHT_SCALE = 1.8
    IMAGE_HEIGHT_DELTA = 0.2
    SCROLL_SPEED = 10
    PRELOAD_WINDOW = 3
    BUFFER_SIZE = (2 * PRELOAD_WINDOW) + 1 # Trying do ensure it's odd

    def __init__(self, parent, *args, **kwargs):
        directory = '~'
        self.directoryPicker = None
        dirSelectWidget = None

        try:
            directory = kwargs.pop('imageDir')
            dirSelectWidget = kwargs.pop('directoryPicker')
        except Exception as e:
            print(str(e))
            exit()

        tk.Frame.__init__(self, parent, *args, **kwargs)

        # get some routine initialization out of the way
        self.parent = parent
        self.parentHeight = parent.winfo_screenheight()
        self.imageHeight = self.IMAGE_HEIGHT_SCALE * self.parentHeight
        self.imageHeightDelta = self.IMAGE_HEIGHT_DELTA * self.parentHeight

        self.canvas = tk.Canvas(self.parent, bd=0, highlightthickness=0)
        self.canvas.create_rectangle(0, 0, self.canvas.winfo_screenwidth(), self.canvas.winfo_screenheight(), fill=BACKGROUND_COLOR)

        frame = tk.Frame(self.canvas)
        
        leftMargin = tk.Frame(self.canvas)
        rightMargin = tk.Frame(self.canvas)

        # Init widget state and data
        self.initData(directory)
        self.image = self.renderImage(0)

        self.pagesLabel = tk.Label(leftMargin, text=self._createPagesText())
        self.pagesLabel.pack()

        self.pageEntry = tk.Entry(leftMargin, width=8)
        self.pageEntry.pack(anchor='w')

        self.pageSubmit = tk.Button(leftMargin, command=self.onPageSubmit, text='Jump')
        self.pageSubmit.pack(anchor='w')

        # Init dir select widget
        self.directoryPicker = dirSelectWidget(rightMargin, directorySelectCallback=self.updateDirectory)
        self.directoryPicker.pack()

        # Init Canvas party
        self.canvas.create_window(0, 0, anchor='nw', window=frame)
        self.canvas.bind_all("<MouseWheel>", self.onScroll)
        self.canvas.bind_all("<Key>", self.keyPress)

        self.canvas.update_idletasks()

        
        leftMargin.pack(anchor='nw', side=tk.LEFT)
        rightMargin.pack(anchor='ne', side=tk.RIGHT)

        self.canvas.pack(fill='both', expand=True)


    def initData(self, directory):
        if not isdir(directory):
            return
        # Otherwise we're good to go!
        self.imageDir = directory
        self.imageIndex = 0

        # Load files in directory
        mangaFiles = [f for f in listdir(self.imageDir) if isfile(join(self.imageDir, f)) and (fnmatch.fnmatch(f, '*.png') or fnmatch.fnmatch(f, '*.jpg'))]
        mangaFiles.sort()

        self.mangaFiles = mangaFiles
        
        # Check for too small of a buffer :P
        if self.BUFFER_SIZE > len(mangaFiles):
            self.BUFFER_SIZE = ((len(mangaFiles) // 2) * 2) + (len(mangaFiles) % 2)
            
            # Assert odd parity
            assert self.BUFFER_SIZE % 2 == 1

            self.PRELOAD_WINDOW = self.BUFFER_SIZE // 2

        self.createImageBuffer(self.imageIndex)


    def createImageBuffer(self, startIndex=0):
        # Create buffer and load images according to configured size
        self.images = [None] * self.BUFFER_SIZE

        # Load initial image
        self.insertImageIntoBuffer(startIndex)

        # Previous images
        for i in range(startIndex - self.PRELOAD_WINDOW, startIndex):
            if i >= 0: self.insertImageIntoBuffer(i)
        
        # Next images
        for i in range(startIndex + 1, startIndex + self.PRELOAD_WINDOW + 1):
            if i < len(self.mangaFiles): self.insertImageIntoBuffer(i)


    def insertImageIntoBuffer(self, imageIndex):
        self.images[imageIndex % self.BUFFER_SIZE] = self.loadMangaImage(imageIndex)

        
    def onScroll(self, event):
        self.canvas.move(self.image, 0, event.delta * self.SCROLL_SPEED)

    def onPageSubmit(self):
        # Remove gross focus
        self.canvas.focus_set()

        # Attempt to jump pages
        userSelection = self.pageEntry.get()

        if userSelection and userSelection.isdigit():
            targetPage = int(userSelection) - 1 # Offset to account for indexing

            self.jumpToIndex(targetPage)

            # Clean up text
            self.pageEntry.delete(0, len(userSelection))

    def updateDirectory(self, newDirectory):
        if not isdir(newDirectory):
            return
        
        # Initialize our data members required for reading
        self.initData(newDirectory)

        # Update the UI to reflect the new data
        self.image = self.renderImage(0)
        self.pagesLabel['text'] = self._createPagesText()


    def keyPress(self, e):
        if e.keycode == KEY_LEFT or e.keycode == KEY_Z:
            self.showNextImage()
        elif e.keycode == KEY_RIGHT or e.keycode == KEY_X:
            self.showPrevImage()
        elif e.keycode == KEY_MINUS:
            self.zoomOut()
        elif e.keycode == KEY_EQUAL:
            self.zoomIn()

    def zoomOut(self):
        self.zoomToHeight(max(10, self.imageHeight - self.imageHeightDelta))

    def zoomIn(self):
        self.zoomToHeight(self.imageHeight + self.imageHeightDelta)

    def zoomToHeight(self, newHeight):
        self.imageHeight = newHeight
        self.createImageBuffer(self.imageIndex)
        self.reloadImage()

    
    def showNextImage(self):
        if self.imageIndex >= len(self.mangaFiles) - 1:
            return
        
        self.changePage(self.imageIndex + 1)


    def showPrevImage(self):
        if self.imageIndex <= 0:
            return
        
        self.changePage(self.imageIndex - 1)

    def jumpToIndex(self, targetIndex):
        if targetIndex < 0 or targetIndex >= len(self.mangaFiles):
            return
        
        self.createImageBuffer(targetIndex)
        self.changePage(targetIndex)

    def reloadImage(self):
        self.changePage(self.imageIndex)

    def removeCurrentImage(self):
        if (self.image): self.canvas.delete(self.image)

    def changePage(self, newIndex):
        # Check oob
        if newIndex < 0 or newIndex >= len(self.mangaFiles):
            return
        # Check availability
        if not self.images[newIndex % self.BUFFER_SIZE]:
            return

        # Delete the current image
        self.removeCurrentImage()

        # Check to see if we can load another image into the buffer
        preloadIndex = -1

        if newIndex > self.imageIndex:
            # Moving ahead
            preloadIndex = newIndex + self.PRELOAD_WINDOW     
        else:
            # Moving back
            preloadIndex = newIndex - self.PRELOAD_WINDOW

        # Check for load validity
        if preloadIndex < len(self.mangaFiles) and preloadIndex >= 0:
            # Load a new image in the buffer
            self.images[preloadIndex % self.BUFFER_SIZE] = self.loadMangaImage(preloadIndex)

        # Update the index
        self.imageIndex = newIndex
        self.image = self.renderImage(newIndex) # display new image and delete
        self.pagesLabel['text'] = self._createPagesText()

    
    def renderImage(self, index=0):
        image = self.getMangaImage(index)
        width = self.parent.winfo_width()
        return self.canvas.create_image(width/2, 0, image=image, anchor='n')


    def loadMangaImage(self, index):
        # Load the image, it's not cached
        imageName = self.mangaFiles[index]
        load = Image.open(join(self.imageDir, imageName))
        width, height = load.size

        # Scale up image if it's kind of small
        scale = (self.parentHeight / height) * self.IMAGE_HEIGHT_SCALE
        newWidth = int(width * scale)
        newHeight = int(height * scale)

        resized = load.resize((newWidth, newHeight), Image.ANTIALIAS)

        resized.thumbnail((self.imageHeight, self.imageHeight), Image.ANTIALIAS)
        return ImageTk.PhotoImage(resized)

    
    def getMangaImage(self, index):
        # Retrieve a manga image from buffer
        # the index will be used mod the length of the buffer
        image = self.images[index % self.BUFFER_SIZE]

        if not image:
            print('Requested image has not been loaded?  No bueno!')
        
        return image


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


class RecentsDialog(tk.Toplevel):
    def __init__(self, parent, items, callback):
        # self.top = tk.Toplevel(parent)

        tk.Toplevel.__init__(self, parent)
        self.transient(parent)

        self.parent = parent

        self.result = None

        self.callback = callback
        self.items = items

        body = tk.Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.initial_focus.focus_set()

        self.wait_window(self)
    
    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden

        self.listbox = tk.Listbox(master=master, selectmode=tk.SINGLE)

        for item in self.items:
            self.listbox.insert(tk.END, item)


        self.listbox.pack()

        return self.listbox

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons

        box = tk.Frame(self)

        w = tk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = tk.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=tk.LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()
    
    def ok(self, event=None):

        self.initial_focus.focus_set() # put focus back
        self.withdraw()
        self.update_idletasks()

        selectedIndex = 0 if not len(self.listbox.curselection()) else self.listbox.curselection()[0]
        self.callback(self.items[selectedIndex])

        self.cancel()

    def cancel(self, event=None):

        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()




class DirSelect(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        try:
            self.directorySelectCallback = kwargs.pop('directorySelectCallback')
        except:
            print('Please supply a callback for directory selection!')
            exit()

        self.directory = kwargs.pop('directory', '~')

        sizex = kwargs.pop('sizex', 80)
        sizey = kwargs.pop('sizey', 60)
        
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.parent = parent
        
        self.root = tk.Frame(self.parent, width=sizex, height=sizey, padx=0, pady=0)

        # Select Button
        self.selectButton = tk.Button(self.root, command=self.openDirectorySelect, text='Select Dir', fg='red')
        self.selectButton.pack()

        # Directory Label
        self.directoryLabel = tk.Label(self.root, text='[N/A]', wraplength=sizex)
        self.directoryLabel.pack()

        # Start Reading Button
        self.readButton = tk.Button(self.root, command=self.startReading, text='Read!', state='disabled')
        self.readButton.pack()

        # Recents button
        self.recentsButton = tk.Button(self.root, command=self.openRecentsSelect, text='Recent')
        self.recentsButton.pack()

        self.root.pack()

    def openRecentsSelect(self):
        x = RecentsDialog(self.parent, recents, self.onDirectorySelect)
        

    def openDirectorySelect(self):
        self.mangaDir = filedialog.askdirectory(initialdir = self.directory,title = "Select Manga Folder")

        if (self._pathIsValid(self.mangaDir)):
            # Update our label and the button state
            self.directoryLabel['text'] = self.mangaDir
            self.readButton['state'] = 'active'

    def startReading(self):

        if (self.mangaDir and os.path.isdir(self.mangaDir) and os.path.exists(self.mangaDir)):
            print('Good to start reading from: ' + str(self.mangaDir))
            self.onDirectorySelect(self.mangaDir)
        else:
            messagebox.showerror("Error", "Please select a manga directory")


    def onDirectorySelect(self, directory):
        print('Saving recent dir')
        saveRecentDir(directory)
        print('executing read callback!')
        self.directorySelectCallback(directory)

    def _pathIsValid(self, path):
        return path and os.path.isdir(path) and os.path.exists(path)




def onSelectCallback(mangaDir):
    global reader
    print('Here goes nothing!')
    reader.updateDirectory(mangaDir)


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


def initSelectGUI(root, directory='~'):
    guiParent = tk.Frame(root)
    guiParent.configure(bg=BACKGROUND_COLOR)

    # Wire up the select section guy
    select = DirSelect(guiParent, directorySelectCallback=onSelectCallback, directory=directory)
    select.pack()

    # Add the logo :)
    logo = Logo(guiParent, path=os.path.join(IMG_PATH, IMG_FILE))
    logo.pack()

    return guiParent


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
    if data[CONFIG_DEFAULT_DIRECTORY_FLAG]:
        DEFAULT_DIRECTORY = data[CONFIG_DEFAULT_DIRECTORY_FLAG]


def saveRecentDir(mangaDir):
    global recents

    if mangaDir in recents:
        # move it up the heirarchy
        index = recents.index(mangaDir)

        recents = [mangaDir] + recents[:index] + recents[(index + 1):]
    else:
        # insert at front and re-assign
        if len(recents) > 5:
            recents = recents[:-1]
        recents.insert(0, mangaDir)

    
    # now we save
    print('Writing: ' + str(recents))
    with open(RECENTS_FILE, 'w') as fout:
        for line in recents:
            fout.write(str(line) + '\n')
            

def loadRecents():
    recents = []

    with open(RECENTS_FILE, 'r') as fin:
        recents = fin.read().splitlines()

    return recents

KEY_ESC = 3473435
KEY_SHIFT_Q = 81
KEY_LEFT = 8124162
KEY_RIGHT = 8189699
KEY_UP = 8320768
KEY_DOWN = 8255233
KEY_MINUS = 1769517
KEY_EQUAL = 1572925
KEY_Z = 393338;
KEY_X = 458872;

BACKGROUND_COLOR = '#5c5c5c'

IMG_PATH = os.path.join('res',)
IMG_FILE = 'logo.jpg'

CONFIG_FILE = 'config.json'
RECENTS_FILE = 'recents.txt'
DEFAULT_DIRECTORY = '~'
CONFIG_DEFAULT_DIRECTORY_FLAG = 'defaultDirectory'


recents = loadRecents()

loadConfig()
loadRecents()
print(DEFAULT_DIRECTORY)


# Set up the root
root = initRoot()  

# Store our widgets in variables
reader = initReader(root, os.path.join('res', 'demo'), DirSelect)

# Begin by showing the directory select
reader.pack()


# Get rocking!
root.mainloop()







print('Running...')


