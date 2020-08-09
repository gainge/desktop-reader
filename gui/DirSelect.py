import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import os
from os.path import isfile, isdir, exists

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
    RECENTS_FILE = 'recents.txt'

    def __init__(self, parent, *args, **kwargs):
        try:
            self.directorySelectCallback = kwargs.pop('directorySelectCallback')
        except:
            print('Please supply a callback for directory selection!')
            exit()

        self.directory = kwargs.pop('directory', '~')

        sizex = kwargs.pop('sizex', 80)
        sizey = kwargs.pop('sizey', 60)

        # Load recents
        self.recents = self.loadRecents(self.RECENTS_FILE)
        
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

    def saveRecentDir(self, mangaDir, recentsPath=RECENTS_FILE):
        if mangaDir in self.recents:
            # move it up the heirarchy
            index = self.recents.index(mangaDir)

            self.recents = [mangaDir] + self.recents[:index] + self.recents[(index + 1):]
        else:
            # insert at front and re-assign
            if len(self.recents) > 5:
                self.recents = self.recents[:-1]
            self.recents.insert(0, mangaDir)

        
        # now we save
        print('Writing: ' + str(self.recents))
        with open(recentsPath, 'w') as fout:
            for line in self.recents:
                fout.write(str(line) + '\n')
                

    def loadRecents(self, recentsPath=RECENTS_FILE):
        loadedRecents = []

        with open(recentsPath, 'r') as fin:
            loadedRecents = fin.read().splitlines()

        return loadedRecents

    def openRecentsSelect(self):
        dialog = RecentsDialog(self.parent, self.recents, self.onDirectorySelect)
        

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
        self.saveRecentDir(directory, self.RECENTS_FILE)
        print('executing read callback!')
        self.directorySelectCallback(directory)

    def _pathIsValid(self, path):
        return path and os.path.isdir(path) and os.path.exists(path)
