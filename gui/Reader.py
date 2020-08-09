import tkinter as tk
import os
from os import listdir
from os.path import isfile, isdir, join
import fnmatch
from PIL import Image, ImageTk
from tkinter import font as tkfont


class Reader(tk.Frame):
    KEY_LEFT = 8124162
    KEY_RIGHT = 8189699
    KEY_UP = 8320768
    KEY_DOWN = 8255233
    KEY_MINUS = 1769517
    KEY_EQUAL = 1572925
    KEY_Z = 393338
    KEY_X = 458872
    KEY_M = 3014765

    SPLASH_SIZE = 500
    SPLASH_TITLE = "Manga Reader"
    SPLASH_SUBTITLE = "Please Select a Directory"
    SPLASH_TEXT_PADDING = 80
    SPLASH_TEXT_COLOR = "#FFF"

    IMAGE_HEIGHT_SCALE = 1.8
    IMAGE_HEIGHT_DELTA = 0.2
    SCROLL_SPEED = 10
    PRELOAD_WINDOW = 3
    BUFFER_SIZE = (2 * PRELOAD_WINDOW) + 1 # Trying do ensure it's odd

    def __init__(self, parent, *args, **kwargs):
        directory = '~'
        self.directoryPicker = None
        dirSelectWidget = None
        self.backgroundColor = None

        try:
            directory = kwargs.pop('imageDir')
            dirSelectWidget = kwargs.pop('directoryPicker')
            self.backgroundColor = kwargs.pop('bg', '#000000')
        except Exception as e:
            print(str(e))
            exit()

        tk.Frame.__init__(self, parent, *args, **kwargs)

        # get some routine initialization out of the way
        self.parent = parent
        self.parentHeight = parent.winfo_screenheight()
        self.imageHeight = self.IMAGE_HEIGHT_SCALE * self.parentHeight
        self.imageHeightDelta = self.IMAGE_HEIGHT_DELTA * self.parentHeight
        self.afterID = None
        self.spreadElements = []
        self.splashElements = []

        self.canvas = tk.Canvas(self.parent, bd=0, highlightthickness=0)

        self.drawBackground()
        self.renderSplash()

        frame = tk.Frame(self.canvas)
        
        leftMargin = tk.Frame(self.canvas)
        rightMargin = tk.Frame(self.canvas)

        # Init widget state and data
        self.imageIndex = -1
        self.mangaFiles = []

        self.pagesLabel = tk.Label(leftMargin, text='N/A')
        self.pagesLabel.pack()

        self.pageEntry = tk.Entry(leftMargin, width=8)
        self.pageEntry.pack(anchor='w')
        self.pageEntry.bind("<Return>", lambda _: self.onPageSubmit())

        self.pageSubmit = tk.Button(leftMargin, command=self.onPageSubmit, text='Jump')
        self.pageSubmit.pack(anchor='w')

        # Init dir select widget
        self.directoryPicker = dirSelectWidget(rightMargin, directorySelectCallback=self.updateDirectory)
        self.directoryPicker.pack()

        # Init Canvas party
        self.canvas.create_window(0, 0, anchor='nw', window=frame)
        self.canvas.bind_all("<MouseWheel>", self.onScroll)
        self.canvas.bind_all("<KeyPress>", self.onKeyPress)
        self.canvas.bind_all("<KeyRelease>", self.onKeyRelease)

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


    def drawBackground(self):
        return self.canvas.create_rectangle(0, 0, self.canvas.winfo_screenwidth(), self.canvas.winfo_screenheight(), fill=self.backgroundColor)

    def renderSplash(self):
        img = self.loadImageFromPath('res/splash.png')
        img.thumbnail((self.SPLASH_SIZE, self.SPLASH_SIZE), Image.ANTIALIAS)

        self.splash = ImageTk.PhotoImage(img)

        xpos = (self.canvas.winfo_screenwidth() / 2) - (self.splash.width() / 2)
        ypos = (self.canvas.winfo_screenheight() / 2) - (self.splash.height() / 2)

        splashID = self.canvas.create_image(xpos, ypos, image=self.splash, anchor='nw')

        # Render some sick text
        titleFont = tkfont.Font(family="Helvetica", size=40, weight="bold")
        subtitleFont = tkfont.Font(family="Helvetica", size = 20)

        titleID = self.canvas.create_text(
            (self.canvas.winfo_screenwidth() / 2),
            (self.canvas.winfo_screenheight() / 2) - (self.splash.height() / 2) - self.SPLASH_TEXT_PADDING,
            text=self.SPLASH_TITLE,
            fill=self.SPLASH_TEXT_COLOR,
            font=titleFont
            )
        subtitleID = self.canvas.create_text(
            (self.canvas.winfo_screenwidth() / 2),
            (self.canvas.winfo_screenheight() / 2) + (self.splash.height() / 2) + self.SPLASH_TEXT_PADDING,
            text=self.SPLASH_SUBTITLE,
            fill=self.SPLASH_TEXT_COLOR,
            font=subtitleFont
            )

        self.splashElements = [splashID, titleID, subtitleID]

    def removeSplash(self):
        for element in self.splashElements:
            self.canvas.delete(element)
        
        self.splashElements = []

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
        if event.state: return
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
        self.removeSplash()
        self.drawBackground()
        self.image = self.renderImage(0)
        self.pagesLabel['text'] = self._createPagesText()


    def onKeyPress(self, e):
        # let's only recognize the m key for now
        if e.keycode == self.KEY_M:
            if self.afterID != None:
                self.after_cancel(self.afterID)
                self.afterID = None
            else:
                self.showSpreadPage()
        elif e.keycode == self.KEY_LEFT or e.keycode == self.KEY_Z:
            self.showNextImage()
        elif e.keycode == self.KEY_RIGHT or e.keycode == self.KEY_X:
            self.showPrevImage()
        elif e.keycode == self.KEY_MINUS:
            self.zoomOut()
        elif e.keycode == self.KEY_EQUAL:
            self.zoomIn()

    def onKeyRelease(self, e):
        if e.keycode == self.KEY_M:
            self.afterID = self.after_idle(self._processKeyRelease, e)
    
    def _processKeyRelease(self, e):
        self.afterID = None
        self.hideSpreadPage()

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



    def showSpreadPage(self):
        if self.imageIndex < 0 or self.imageIndex >= len(self.mangaFiles) or len(self.mangaFiles) <= 1:
            return # Don't mess with edge cases and w/e

        
        # Create widgets
        bg = self.drawBackground()
        
        # Load images @ correct size
        leftImageIndex = min(len(self.mangaFiles) - 1, self.imageIndex + 1)
        self.leftImage = self.loadMangaImage(leftImageIndex, 1)
        self.rightImage = self.loadMangaImage(leftImageIndex - 1, 1)
        
        # Display and store
        width = self.parent.winfo_width()
        offset = (width / 2) - self.leftImage.width()
        leftPanel = self.canvas.create_image((width / 4) + (offset / 2), 0, image=self.leftImage, anchor='n')
        rightPanel = self.canvas.create_image(((3 * width) / 4) - (offset / 2), 0, image=self.rightImage, anchor='n')

        # Add the ids to our list for safekeeping
        self.spreadElements = [bg, leftPanel, rightPanel]
    

    def hideSpreadPage(self):
        # Remove temporary display
        for elementID in self.spreadElements:
            self.canvas.delete(elementID)

        self.spreadElements = []

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
            self.insertImageIntoBuffer(preloadIndex)

        # Update the index
        self.imageIndex = newIndex
        self.image = self.renderImage(newIndex) # display new image and delete
        self.pagesLabel['text'] = self._createPagesText()

    
    def renderImage(self, index=0):
        image = self.getMangaImage(index)
        width = self.parent.winfo_width()
        return self.canvas.create_image(width/2, 0, image=image, anchor='n')


    def loadMangaImage(self, index, heightScale=IMAGE_HEIGHT_SCALE):
        # Load the image, it's not cached
        imageName = self.mangaFiles[index]
        load = self.loadImageFromPath(join(self.imageDir, imageName))

        # Scale up image if it's kind of small
        resized = self.scaleImage(load, heightScale)

        resized.thumbnail((self.imageHeight, self.imageHeight), Image.ANTIALIAS)
        return ImageTk.PhotoImage(resized)


    def loadImageFromPath(self, imagePath):
        return Image.open(imagePath)

    def scaleImage(self, image, ratio=IMAGE_HEIGHT_SCALE):
        width, height = (None, None)

        if hasattr(image, 'size'):
            width, height = image.size
        else:
            width = int(image.width())
            height = int(image.height())

        scale = (self.canvas.winfo_height() / height) * ratio
        newWidth = int(width * scale)
        newHeight = int(height * scale)

        return image.resize((newWidth, newHeight), Image.ANTIALIAS)
    
    def getMangaImage(self, index):
        # Retrieve a manga image from buffer
        # the index will be used mod the length of the buffer
        image = self.images[index % self.BUFFER_SIZE]

        if not image:
            print('Requested image has not been loaded?  No bueno!')
        
        return image


    def _createPagesText(self):
        return f"{self.imageIndex + 1} / {len(self.mangaFiles)}"
