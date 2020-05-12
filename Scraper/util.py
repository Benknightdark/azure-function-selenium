from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import json
import requests
import msal

config = {'scope': ['user.read','files.readwrite.all','sites.readwrite.all'], 
          'endpoint': 'https://graph.microsoft.com/v1.0/users/{}/drive/root:/Harmony_csv'.format(os.environ['username']),
          'client_id': os.environ['client_id'],
          'username': os.environ['username'],
          'password': os.environ['password_m'],
          'authority': 'https://login.microsoftonline.com/organizations'}

class Segment:
    """
    Navigates through the ChromeDriver, encoding username and password, and clicking buttons
    """
    
    def __init__(self, driver, EC, 
                element_find, element_click, element_next = None, 
                element_input = None, input = None):
        """
        Creates a new instance of the Segment
        :Args:
        element_find - element that you are searching for
        element_click - element that you will be clicking
        element_next - element that you expect to see after clicking
        element_input - element where you will be encoding input
        input - what you want to encode
        """

        # Waits for the element to be clickable
        self.previous_driver = driver
        self.element = WebDriverWait(self.previous_driver, 30).until(EC.element_to_be_clickable((By.XPATH, element_find)))
       
       # For username and password
        if input != "":
            self.previous_driver \
                .find_element_by_xpath(element_input) \
                .send_keys(input)
        else:
            pass
        
        # Clicks the button
        self.button = self.previous_driver.find_element_by_xpath(element_click) \
                            .click()
        
        # Waits for the next element to appear
        if element_next != "":
             self.element = WebDriverWait(self.previous_driver, 30).until(lambda x: x.find_element_by_xpath(element_next))
        else:
            pass
        
        # Sets the current driver
        self.driver = self.previous_driver

def Initialize():
    """
    Initializes a webdriver object and opens the Tealeaf page
    """

    # Setting Options
    print('Opening chrome')
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images":2, \
             "download.default_directory": os.environ["DATA_PATH"]}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # Makes the webdriver object
    init_driver = webdriver.Chrome("/usr/local/bin/chromedriver", chrome_options = chrome_options)
    init_driver.get('https://tealeaf-us-2.goacoustic.com/webapp/home#/intelli-search')

    return init_driver

def Upload():
    """
    Set-up credentials for Graph API
    """

    # authenticate
    app = msal.PublicClientApplication(config['client_id'], authority=config['authority'])
    result = None
    
    # check cache to see if end user has signed in before
    accounts = app.get_accounts(username=config['username'])

    # get access token
    result = app.acquire_token_by_username_password(config["username"], config['password'], scopes=config['scope'])

    # set headers
    headers = {'Authorization': 'Bearer ' + result['access_token']}

    # Uploading file
    print("Uploading file to Harmony_csv")
    for root, dirs, files in os.walk(os.environ['DATA_PATH']):
        for filename in files:
            filepath = os.path.join(root, filename)
            print("Uploading " + filename)
            fileHandle = open(filepath, 'rb')
            r = requests.put(config["endpoint"] + '/' + filename + ':/content', data=fileHandle, headers = headers)
            fileHandle.close()
            
            if r.status_code == 200 or r.status_code ==201:
                # Remove content
                os.remove(filepath)
                print("Original file deleted")