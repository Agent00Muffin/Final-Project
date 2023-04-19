""" 
COMP 593 - Final Project

Description: 
  Downloads NASA's Astronomy Picture of the Day (APOD) from a specified date
  and sets it as the desktop background image.

Usage:
  python apod_desktop.py [apod_date]

Parameters:
  apod_date = APOD date (format: YYYY-MM-DD)
"""
import re
import datetime
import os
import sys
import image_lib
import inspect
import sqlite3
import apod_api
import hashlib



# Global variables
image_cache_dir = None  # Full path of image cache directory
image_cache_db = None   # Full path of image cache database

def main():
    ## DO NOT CHANGE THIS FUNCTION ##
    # Get the APOD date from the command line
    apod_date = get_apod_date()    

    # Get the path of the directory in which this script resides
    script_dir = get_script_dir()

    # Initialize the image cache
    init_apod_cache(script_dir)

    # Add the APOD for the specified date to the cache
    apod_id = add_apod_to_cache(apod_date)

    # Get the information for the APOD from the DB
    apod_info = get_apod_info(apod_id)

    # Set the APOD as the desktop background image
    if apod_id != 0:
        image_lib.set_desktop_background_image(apod_info['file_path'])

def get_apod_date():
    """Gets the APOD date
     
    The APOD date is taken from the first command line parameter.
    Validates that the command line parameter specifies a valid APOD date.
    Prints an error message and exits script if the date is invalid.
    Uses today's date if no date is provided on the command line.

    Returns:
        date: APOD date
    """

    today = datetime.date.today()
    start_date = datetime.date(1995, 6, 16)

    if len(sys.argv) > 1:
        try:
            clean_date = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d').date()

            if today < clean_date:
                print('Error: APOD date cannor be in the future')
                print('Script execution aborted')
                sys.exit()
            elif clean_date < start_date:
                print('Error: APOD date cannor be earlier than 1995-06-16')
                print('Script execution aborted')
                sys.exit()
            elif today >= clean_date >= start_date:
                apod_date = clean_date
            
        except ValueError:
            print(f'Error: Invalid date format; Invalid isoformat string: {sys.argv[1]}')
            print('Script execution aborted')
            sys.exit()
    else:
        apod_date = datetime.date.today().isoformat()
    return apod_date

def get_script_dir():
    """Determines the path of the directory in which this script resides

    Returns:
        str: Full path of the directory in which this script resides
    """
    ## DO NOT CHANGE THIS FUNCTION ##
    script_path = os.path.abspath(inspect.getframeinfo(inspect.currentframe()).filename)
    return os.path.dirname(script_path)

def init_apod_cache(parent_dir):
    """Initializes the image cache by:
    - Determining the paths of the image cache directory and database,
    - Creating the image cache directory if it does not already exist,
    - Creating the image cache database if it does not already exist.
    
    The image cache directory is a subdirectory of the specified parent directory.
    The image cache database is a sqlite database located in the image cache directory.

    Args:
        parent_dir (str): Full path of parent directory    
    """
    global image_cache_dir
    global image_cache_db
    # Find correct directory
    image_cache_dir = parent_dir + r'\image_cache'
    print(f'Image cache directory: {image_cache_dir}')

    # check if the file directory "\image_cache" exists
    if os.path.isdir(image_cache_dir):
        print('Image cache directory already exists.')
    else:
        # file dir does not exist, create it
        print('Image cache directory created.')
        os.mkdir(image_cache_dir)

    # find correct directory
    image_cache_db = image_cache_dir + r'\image_cache.db'
    print(f'Image cache DB: {image_cache_db}')

    # Check if the image cache DB exists
    if os.path.isfile(image_cache_db):
        print('Image cache DB already exists.')
    else:
        # Create DB and commit the created table
        con = sqlite3.connect(image_cache_db)
        cur = con.cursor()
        table = """CREATE TABLE IF NOT EXISTS cache 
        (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            explanation TEXT NOT NULL,
            file_path TEXT NOT NULL,
            sha256 TEXT NOT NULL
        );"""
        cur.execute(table)
        con.commit()
        con.close()
        print('Image cache DB created.')


def add_apod_to_cache(apod_date):
    """Adds the APOD image from a specified date to the image cache.
     
    The APOD information and image file is downloaded from the NASA API.
    If the APOD is not already in the DB, the image file is saved to the 
    image cache and the APOD information is added to the image cache DB.

    Args:
        apod_date (date): Date of the APOD image

    Returns:
        int: Record ID of the APOD in the image cache DB, if a new APOD is added to the
        cache successfully or if the APOD already exists in the cache. Zero, if unsuccessful.
    """
    print("APOD date:", apod_date)

    apod_data = apod_api.get_apod_info(apod_date)


    title = apod_data['title']
    print(f'APOD title: {title}')
    explanation = apod_data['explanation']
    image_url = apod_api.get_apod_image_url(apod_data)
    
    print(f'APOD URL: {image_url}')

    # Download the APOD image
    apod_downloaded = image_lib.download_image(image_url)
    
    sha256 = hashlib.sha256(apod_downloaded).hexdigest()
    print(f'APOD SHA-265: {sha256}')

    query_result = get_apod_id_from_db(sha256)
    file_path = determine_apod_file_path(title, image_url)

    if query_result != 0:
        print('APOD image is already in cache')
        return query_result
    elif query_result == 0:
        print('APOD image is not already in cache.')
        print(f'APOD file path: {file_path}')
        image_lib.save_image_file(apod_downloaded, file_path)
        print('Adding APOD to image cache DB...', end='')

    # Add the APOD info to the DB
        apod_info = add_apod_to_db(title, explanation, file_path, sha256)
        return apod_info
    else:
        return 0

def add_apod_to_db(title, explanation, file_path, sha256):
    """Adds specified APOD information to the image cache DB.
     
    Args:
        title (str): Title of the APOD image
        explanation (str): Explanation of the APOD image
        file_path (str): Full path of the APOD image file
        sha256 (str): SHA-256 hash value of APOD image

    Returns:
        int: The ID of the newly inserted APOD record, if successful.  Zero, if unsuccessful       
    """
    print('Adding APOD to image cache DB...', end='')
    con = sqlite3.connect(image_cache_db)
    cur = con.cursor()
    image_cache_query = """INSERT INTO cache
        (
            title,
            explanation,
            file_path,
            sha256
        ) 
        VALUES (?, ?, ?, ?);"""
    cache_datas = (title, explanation, file_path, sha256)
    cur.execute(image_cache_query, cache_datas)
    con.commit()
    con.close()
    last_row_id = cur.lastrowid
    # Check most recently created entry
    if last_row_id > 0: 
        print('success')
        return last_row_id
    else:
        print('failure')
        return 0

def get_apod_id_from_db(image_sha256):
    """Gets the record ID of the APOD in the cache having a specified SHA-256 hash value
    
    This function can be used to determine whether a specific image exists in the cache.

    Args:
        image_sha256 (str): SHA-256 hash value of APOD image

    Returns:
        int: Record ID of the APOD in the image cache DB, if it exists. Zero, if it does not.
    """
    con = sqlite3.connect(image_cache_db)
    cur = con.cursor()
    cur.execute(f'SELECT id FROM cache WHERE sha256="{image_sha256}"')
    query_result = cur.fetchone()
    con.close()
    if query_result == None:
        return 0 
    else:
        return query_result[0]

def determine_apod_file_path(image_title, image_url):
    """Determines the path at which a newly downloaded APOD image must be 
    saved in the image cache. 
    
    The image file name is constructed as follows:
    - The file extension is taken from the image URL
    - The file name is taken from the image title, where:
        - Leading and trailing spaces are removed
        - Inner spaces are replaced with underscores
        - Characters other than letters, numbers, and underscores are removed

    For example, suppose:
    - The image cache directory path is 'C:\\temp\\APOD'
    - The image URL is 'https://apod.nasa.gov/apod/image/2205/NGC3521LRGBHaAPOD-20.jpg'
    - The image title is ' NGC #3521: Galaxy in a Bubble '

    The image path will be 'C:\\temp\\APOD\\NGC_3521_Galaxy_in_a_Bubble.jpg'

    Args:
        image_title (str): APOD title
        image_url (str): APOD image URL
    
    Returns:
        str: Full path at which the APOD image file must be saved in the image cache directory
    """
    # get the file extension from the image URL
    file_ext = os.path.splitext(image_url)[1]
    
    # remove characters other than letters, numbers, and underscores from the image title
    clean_title = re.sub(r'[^\w\s]','',image_title).strip().replace(' ', '_')
    
    # construct the image file path
    file_path = os.path.join(image_cache_dir + "\\" + f"{clean_title}{file_ext}")
    
    return file_path

def get_apod_info(image_id):
    """Gets the title, explanation, and full path of the APOD having a specified
    ID from the DB.

    Args:
        image_id (int): ID of APOD in the DB

    Returns:
        dict: Dictionary of APOD information
    """
    con = sqlite3.connect(image_cache_db)
    cur = con.cursor()
    cur.execute(f"SELECT title, explanation, file_path FROM cache WHERE id='{image_id}'")
    query_result = cur.fetchone()
    con.close()

    apod_info = {
        'title': query_result[0],
        'explanation': query_result[1],
        'file_path': query_result[2]
    }
    return apod_info

def get_all_apod_titles():
    """Gets a list of the titles of all APODs in the image cache

    Returns:
        list: Titles of all images in the cache
    """
    # NOTE: This function is only needed to support the APOD viewer GUI
    con = sqlite3.connect(image_cache_db)
    cur = con.cursor()
    cur.execute(f"SELECT title FROM cache")
    title_list = cur.fetchall()
    con.close()
    return title_list

if __name__ == '__main__':
    main()