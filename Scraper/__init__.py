# import packages
import azure.functions as func
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from time import sleep
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

def Navigate(*args_tuple):
    """
    Driver navigates through the webpage
    """
    retries = 0
    args = list(args_tuple)
    if len(args)== 5:
        args.append("")
        args.append("")

    while True:
        try:
            class_object = Segment(args[0], args[1], args[2], args[3], args[4], args[5], args[6])
            break
        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):

            # Restart the whole process after 2 tries
            if retries <= 1:
                print('Retrying')
                retries += 1
                continue
            else:
                print('Restarting')
                init_driver.close()
                init_driver.quit()
                main()
                exit()

    return class_object

def main(mytimer: func.TimerRequest) -> None:
    global init_driver
    init_driver = Initialize()

    # click button to log in using IBM Id
    print('Log-in using IBM Id')
    log_in_IBM = Navigate(init_driver \
                                ,EC \
                                ,'.//button[@class = "login-with-ibmId-button-inside"]' \
                                ,'.//button[@class = "login-with-ibmId-button-inside"]' \
                                ,'.//button[@id = "continue-button"]'
    )

    # input username/email then continue
    print('Encoding username')
    input_username = Navigate(log_in_IBM.driver \
                                    ,EC \
                                    ,'.//button[@id = "continue-button"]' \
                                    ,'.//button[@id = "continue-button"]' \
                                    ,'.//button[@id = "signinbutton"]' \
                                    ,'.//input[@id = "username"]' \
                                    ,os.environ["username"]
    )

    # input password then continue
    print('Encoding password')
    input_password = Navigate(input_username.driver \
                            ,EC \
                            ,'.//button[@id = "signinbutton"]' \
                            ,'.//button[@id = "signinbutton"]' \
                            ,'.//a[@title = "Mobile-Project Harmony"]' \
                            ,'.//input[@id = "password"]' \
                            ,os.environ["password"]
    )
    
    # open tealeaf session search webpage
    print('Opening session')
    session_search = Navigate(input_password.driver \
                            ,EC \
                            ,'.//span[contains(@ng-click,"search()")]' \
                            ,'.//span[contains(@ng-click,"search()")]' \
                            ,'.//th[contains(@title, "Session Start Time")]'
    )
    
    # set application to Project Harmony
    print('Setting app to Project Harmony')
    application_1 = Navigate(session_search.driver \
                            ,EC \
                            ,'.//div[contains(@class, "app-info")]' \
                            ,'.//div[contains(@class, "app-info")]' \
                            ,'.//a[contains(@tabindex,"-1") and contains(@title,"Project Harmony")]'
    )

    application_2 = Navigate(application_1.driver \
                            ,EC \
                            ,'.//a[contains(@tabindex,"-1") and contains(@title,"Project Harmony")]' \
                            ,'.//a[contains(@tabindex,"-1") and contains(@title,"Project Harmony")]' \
                            ,'.//div[@class = "sess-time-menu"]'
    )

    # set Session Time to 15 minutes
    print('Set session time to 15 minutes')
    session_time_1 = Navigate(application_2.driver \
                           ,EC \
                           ,'.//div[@class = "sess-time-menu"]' \
                           ,'.//div[@class = "sess-time-menu"]' \
                           ,'.//div[contains(@ng-if,"!period.template") and contains(@translate,"Last 15 minutes")]'
    )
    
    session_time_2 = Navigate(session_time_1.driver \
                            ,EC \
                            ,'.//div[contains(@ng-if,"!period.template") and contains(@translate,"Last 15 minutes")]' \
                            ,'.//div[contains(@ng-if,"!period.template") and contains(@translate,"Last 15 minutes")]' \
                            ,'.//span[contains(@class,"current-viewname ng-binding")]'
    )
    
    # change view to Harmony
    print('Change view to Harmony')
    views = Navigate(session_time_2.driver \
                        ,EC \
                        ,'.//span[contains(@class,"current-viewname ng-binding")]' \
                        ,'.//span[contains(@class,"current-viewname ng-binding")]' \
                        ,'.//div[contains(@class,"view-title") and contains(@ng-click,"showPublicViews()")]'
    )

    public_views = Navigate(views.driver \
                        ,EC \
                        ,'.//div[contains(@class,"view-title") and contains(@ng-click,"showPublicViews()")]' \
                        ,'.//div[contains(@class,"view-title") and contains(@ng-click,"showPublicViews()")]' \
                        ,'.//li[contains(@ng-repeat,"view in publicViews")]/span[contains(.,"Harmony")]'
    )
    
    public_views_Harmony = Navigate(public_views.driver \
                        ,EC \
                        ,'.//li[contains(@ng-repeat,"view in publicViews")]/span[contains(.,"Harmony")]' \
                        ,'.//li[contains(@ng-repeat,"view in publicViews")]/span[contains(.,"Harmony")]' \
                        ,'.//span[contains(@ng-click,"searchForResultClick()")]'
    )

    # search results
    print('Searching for results')
    search_result = Navigate(public_views_Harmony.driver \
                            ,EC \
                            ,'.//span[contains(@ng-click,"searchForResultClick()")]' \
                            ,'.//span[contains(@ng-click,"searchForResultClick()")]' \
                            ,'.//span[contains(@ng-click,"setDisplayLimit(2500)")]'
    )

    results_2500 = Navigate(search_result.driver \
                            ,EC \
                            ,'.//span[contains(@ng-click,"setDisplayLimit(2500)")]' \
                            ,'.//span[contains(@ng-click,"setDisplayLimit(2500)")]' \
                            ,'.//div[contains(@style,"padding-top:4px;") and contains(@class, "pull-right template-menu")]'
    )
    
    # export results
    print('Exporting Results')
    export_results = Navigate(results_2500.driver \
                            ,EC \
                            ,'.//div[contains(@style,"padding-top:4px;") and contains(@class, "pull-right template-menu")]' \
                            ,'.//div[contains(@style,"padding-top:4px;") and contains(@class, "pull-right template-menu")]' \
                            ,'.//a[contains(@ng-click,"downloadCSV()")]'
    )
    
    export_csv = Navigate(export_results.driver \
                            ,EC \
                            ,'.//a[contains(@ng-click,"downloadCSV()")]' \
                            ,'.//a[contains(@ng-click,"downloadCSV()")]' \
                            ,'.//div[contains(@style,"padding-top:4px;") and contains(@class, "pull-right template-menu")]'
    )
    print('File saved')
    sleep(1)
    init_driver.close()
    init_driver.quit()
    Upload()
    print('Done Uploading')





