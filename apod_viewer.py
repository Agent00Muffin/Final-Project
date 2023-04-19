from tkinter import *
from tkinter import ttk
import datetime as dt
import image_lib
import ctypes
import inspect
import os
import apod_desktop
from tkcalendar import *
import sqlite3
from PIL import Image, ImageTk

# Determine the path and parent directory of this script
script_path = os.path.abspath(inspect.getframeinfo(inspect.currentframe()).filename)
script_dir = os.path.dirname(script_path)

# Initialize the image cache
apod_desktop.init_apod_cache(script_dir)

# TODO: Create the GUI
root = Tk()
root.geometry()
root.title("Astronomy Picture of the Day Viewer")
root.resizable(True, True)
root.rowconfigure(0, weight=75)
root.rowconfigure(1, weight=75)
root.columnconfigure(0, weight=75)
root.columnconfigure(1, weight=75)

# set window icon
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('COMP593.NASAAPODImageViewer') # Taskbar icon still not working
icon_path = os.path.join(script_dir, 'nasa.ico')
root.iconbitmap(icon_path)

# add frames 
frm_top = ttk.Frame(root)
frm_top.grid(row=0, column=0, columnspan=2, padx=15, pady=20, sticky=NSEW)
frm_top.rowconfigure(0, weight=75)
frm_top.columnconfigure(0, weight=75)

frm_btm_left = ttk.LabelFrame(root, text='View Cached Image')
frm_btm_left.grid(row=1, column=0, padx=15, pady=20, sticky=NSEW)
frm_btm_left.rowconfigure(0, weight=75)
frm_btm_left.columnconfigure(0, weight=75)

frm_btm_right = ttk.LabelFrame(root, text='Get More Images')
frm_btm_right.grid(row=1, column=1, padx=15, pady=20, sticky=NSEW)
frm_btm_right.rowconfigure(0, weight=75)
frm_btm_right.columnconfigure(0, weight=75)

# add text boxes
img_lbl = ttk.Label(frm_btm_left, text='Select Image:')
img_lbl.grid(row=0, column=0, padx=15, pady=20, sticky=NSEW)

date_lbl = ttk.Label(frm_btm_right, text='Select Date:')
date_lbl.grid(row=0, column=0, padx=15, pady=20, sticky=NSEW)

# add date entry widget
date_min = dt.date(1995, 6, 16)
date_max = dt.date.today()
cal = DateEntry(frm_btm_right, mindate=date_min, maxdate=date_max)
cal.grid(row=0, column=1)

# add image into frame
path = os.path.join(script_dir, 'nasa.png')
logo = Image.open(path)
nasa_img = ImageTk.PhotoImage(logo)
lbl_image = ttk.Label(frm_top, image=nasa_img)
lbl_image.grid(row=0, column=0)



# Pull-down list of past apod titles
title_list = sorted(apod_desktop.get_all_apod_titles())
img_menu = ttk.Combobox(frm_btm_left, value=title_list, state='readonly')
img_menu.set("Select an Image")
img_menu.grid(row=0, column=1, padx=15, pady=20)


def handle_set_desktop():  
    # Sets desktop background
    global path
    image_lib.set_desktop_background_image(path)

def handle_image_select(event):
    past_image = img_menu.get()
    if past_image:
        image_db = apod_desktop.image_cache_db
        con = sqlite3.connect(image_db)
        cur = con.cursor()
        query = """SELECT explanation, file_path FROM cache WHERE title=?"""
        cur.execute(query, (past_image,))
        query_result = cur.fetchone()
        con.close()
        if query_result:
            explanation = query_result[0]
            path = query_result[1]
            return explanation, path
    return None, None

img_menu.bind('<<ComboboxSelected>>', handle_image_select)

def get_date():
    global path
    date = cal.get_date().strftime('%Y-%m-%d')
    apod_id = apod_desktop.add_apod_to_cache(date) 
    apod_dict = apod_desktop.get_apod_info(apod_id)
    path = apod_dict['file_path']
    print(path)
    title = apod_dict['title']
    explanation = apod_dict['explanation']
    title_list.append(title)
    update_image(explanation, path, title)

lbl_exp = ttk.Label(frm_top, text=None, wraplength=1500)
lbl_exp.grid(row=1, column=0, padx=20, pady=20, sticky=NSEW)

def update_image(explantion, file_path, title=None):
    # replace icon/image with selected image
    sel_image = Image.open(file_path)
    max_size = (1280, 960)
    sel_image.thumbnail(max_size)
    current_img = ImageTk.PhotoImage(sel_image)
    lbl_image.configure(image=current_img)
    lbl_image.image = current_img
    lbl_exp.config(text=explantion)
    # title check/fix
    if title is not None:
        img_menu.set(title)

background_button = Button(frm_btm_left, text='Set as Desktop', command=handle_set_desktop)
background_button.grid(row=0, column=2, padx=20, pady=20)

download_button = Button(frm_btm_right, text='Download Image', command=get_date)
download_button.grid(row=0, column=2, padx=20, pady=20)


root.mainloop()
