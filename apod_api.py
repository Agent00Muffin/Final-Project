'''
Library for interacting with NASA's Astronomy Picture of the Day API.
'''
import requests
def main():
    # test the functions in this module
    apod_data = get_apod_info('2001-06-25')
    get_apod_image_url(apod_data)
    return

def get_apod_info(apod_date):
    """Gets information from the NASA API for the Astronomy 
    Picture of the Day (APOD) from a specified date.

    Args:
        apod_date (date): APOD date (Can also be a string formatted as YYYY-MM-DD)

    Returns:
        dict: Dictionary of APOD info, if successful. None if unsuccessful
    """
    API_KEY = 'lcMnl4LyVsmkRvr4RiiL9l7viVaWbq1nhPxnHOeG'
    APOD_API = 'https://api.nasa.gov/planetary/apod'
    query_params = {
        'api_key': API_KEY,
        'date': apod_date,
        'thumbs': True,
    }
    # attempt to gather data from the APOD API
    print(f'Getting {apod_date} APOD information from NASA...', end='')
    API_resp = requests.get(APOD_API, params=query_params)
    if API_resp.ok:
        print('Success')
        apod_info_dict = API_resp.json()
        return apod_info_dict
    else:
        print('Failure')
        return

def get_apod_image_url(apod_info_dict):
    """Gets the URL of the APOD image from the dictionary of APOD information.

    If the APOD is an image, gets the URL of the high definition image.
    If the APOD is a video, gets the URL of the video thumbnail.

    Args:
        apod_info_dict (dict): Dictionary of APOD info from API

    Returns:
        str: APOD image URL
    """
    # Check if the media is a video or image.
    media = apod_info_dict['media_type']
    if media == 'video':
        url = apod_info_dict['thumbnail_url']
        return url
    else:
        url = apod_info_dict['hdurl']
        return url
if __name__ == '__main__':
    main()