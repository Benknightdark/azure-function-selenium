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

PROJECT_NAME = "Harmony"
URL = 'https://tealeaf-us-2.goacoustic.com/webapp/home#/intelli-search'
CONFIG = {'scope': ['user.read','files.readwrite.all','sites.readwrite.all'], 
          'endpoint': f"https://graph.microsoft.com/v1.0/users/{os.environ['username']}/drive/root:/{PROJECT_NAME}_csv",
          'client_id': os.environ['client_id'],
          'username': os.environ['username'],
          'password': os.environ['password'],
          'password_m': os.environ['password_m'],
          'authority': 'https://login.microsoftonline.com/organizations'}
CHROMEDRIVER = "/usr/local/bin/chromedriver"

class Scraper:
    """
    Creates a Scraper object to scrape Tealeaf
    """

    def __init__(self, projectName, url, config, chromedriver):
        self.projectName = projectName
        self.url = url
        self.config = config
        self.chromedriver = chromedriver


    class Segment:
        """
        scraper.navigates through the ChromeDriver, encoding username and password, and clicking buttons
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
            if input != None:
                self.previous_driver \
                    .find_element_by_xpath(element_input) \
                    .send_keys(input)
            else:
                pass
            
            # Clicks the button
            print("clicking")
            self.button = self.previous_driver.find_element_by_xpath(element_click) \
                                .click()
            
            # Waits for the next element to appear
            print("waiting")
            if element_next != None:
                 self.element = WebDriverWait(self.previous_driver, 30).until(lambda x: x.find_element_by_xpath(element_next))
            else:
                pass
            
            # Sets the current driver
            self.driver = self.previous_driver


    def initialize(self):
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
        chrome_options.add_argument('window-size=1200x1040')
        chrome_options.add_argument('--disable-dev-shm-usage')

        # Makes the webdriver object
        init_driver = webdriver.Chrome(CHROMEDRIVER, chrome_options = chrome_options)
        init_driver.get(self.url)
        self.init_driver = init_driver

    def navigate(self, *args):
        """
        Driver navigates through the webpage
        """
        retries = 0
        while True:
            try:
                class_object = self.Segment(*args)
                break
            except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
                
                # Restart the whole process after 2 tries
                if retries <= 1:
                    print('Retrying')
                    retries += 1
                    continue
                else:
                    print('Restarting')
                    self.init_driver.close()
                    self.init_driver.quit()
                    main()
                    exit()

        return class_object

    
    def upload(self):
        """
        Set-up credentials for Graph API
        """

        # authenticate
        app = msal.PublicClientApplication(self.config['client_id'], authority=self.config['authority'])
        result = None
        
        # check cache to see if end user has signed in before
        accounts = app.get_accounts(username=self.config['username'])

        # get access token
        result = app.acquire_token_by_username_password(self.config["username"], self.config['password_m'], scopes=self.config['scope'])

        # set headers
        headers = {'Authorization': 'Bearer ' + result['access_token']}

        # Uploading file
        print(f"Uploading file to {PROJECT_NAME}_csv")
        for root, dirs, files in os.walk(os.environ['DATA_PATH']):
            for filename in files:
                filepath = os.path.join(root, filename)
                print("Uploading " + filename)
                with open(filepath, 'rb') as fileHandle:
                    r = requests.put(self.config["endpoint"] + '/' + filename + ':/content', data=fileHandle, headers = headers)
                
                if r.status_code == 200 or r.status_code ==201:
                    # Remove content
                    os.remove(filepath)
                    print("Original file deleted")

def main(mytimer: func.TimerRequest) -> None:
    scraper = Scraper(PROJECT_NAME, URL, CONFIG, CHROMEDRIVER)
    scraper.initialize()

    # click button to log in using IBM Id
    print('Log-in using IBM Id')
    log_in_IBM = scraper.navigate(scraper.init_driver \
                                ,EC \
                                ,'//div[contains(@class, "login-with-ibmId")]' \
                                ,'//div[contains(@class, "login-with-ibmId")]' \
                                ,'.//button[@id = "continue-button"]'
    )

    # input username/email then continue
    print('Encoding username')
    input_username = scraper.navigate(log_in_IBM.driver \
                                    ,EC \
                                    ,'.//button[@id = "continue-button"]' \
                                    ,'.//button[@id = "continue-button"]' \
                                    ,'.//button[@id = "signinbutton"]' \
                                    ,'.//input[@id = "username"]' \
                                    ,CONFIG['username']
    )
    # input password then continue

    print('Encoding password')
    input_password = scraper.navigate(input_username.driver \
                            ,EC \
                            ,'.//button[@id = "signinbutton"]' \
                            ,'.//button[@id = "signinbutton"]' \
                            ,'.//span[contains(@ng-click,"searchForResultClick")]' \
                            ,'.//input[@id = "password"]' \
                            ,CONFIG['password']
    )
    
    # open tealeaf session search webpage
    print('Opening session')
    session_search = scraper.navigate(input_password.driver \
                            ,EC \
                            ,'.//span[contains(@ng-click,"searchForResultClick")]' \
                            ,'.//span[contains(@ng-click,"searchForResultClick")]' \
                            ,'.//th[contains(@title, "Session Start Time")]'
    )
    
    # set application to Project {PROJECT_NAME}
    print(f'Setting app to Project {PROJECT_NAME}')
    application_1 = scraper.navigate(session_search.driver \
                            ,EC \
                            ,'.//div[contains(@class, "app-info")]' \
                            ,'.//div[contains(@class, "app-info")]' \
                            ,f'.//a[contains(@tabindex,"-1") and contains(@title,"Project {PROJECT_NAME}")]'
    )

    application_2 = scraper.navigate(application_1.driver \
                            ,EC \
                            ,f'.//a[contains(@tabindex,"-1") and contains(@title,"Project {PROJECT_NAME}")]' \
                            ,f'.//a[contains(@tabindex,"-1") and contains(@title,"Project {PROJECT_NAME}")]' \
                            ,'.//div[@class = "sess-time-menu"]'
    )

    # set Session Time to 15 minutes
    print('Set session time to 15 minutes')
    session_time_1 = scraper.navigate(application_2.driver \
                           ,EC \
                           ,'.//div[@class = "sess-time-menu"]' \
                           ,'.//div[@class = "sess-time-menu"]' \
                           ,'.//div[contains(@ng-if,"!period.template") and contains(@translate,"Last 15 minutes")]'
    )

    session_time_2 = scraper.navigate(session_time_1.driver \
                            ,EC \
                            ,'.//div[contains(@ng-if,"!period.template") and contains(@translate,"Last 15 minutes")]' \
                            ,'.//div[contains(@ng-if,"!period.template") and contains(@translate,"Last 15 minutes")]' \
                            ,'.//span[contains(@class,"current-viewname ng-binding")]'
    )
    
    # change view to {PROJECT_NAME}
    print(f'Change view to {PROJECT_NAME}')
    views = scraper.navigate(session_time_2.driver \
                        ,EC \
                        ,'.//span[contains(@class,"current-viewname ng-binding")]' \
                        ,'.//span[contains(@class,"current-viewname ng-binding")]' \
                        ,'.//div[contains(@class,"view-title") and contains(@ng-click,"showPublicViews()")]'
    )

    public_views = scraper.navigate(views.driver \
                        ,EC \
                        ,'.//div[contains(@class,"view-title") and contains(@ng-click,"showPublicViews()")]' \
                        ,'.//div[contains(@class,"view-title") and contains(@ng-click,"showPublicViews()")]' \
                        ,f'.//li[contains(@ng-repeat,"view in publicViews")]/span[contains(.,"{PROJECT_NAME}")]'
    )

    public_views_project = scraper.navigate(public_views.driver \
                        ,EC \
                        ,f'.//li[contains(@ng-repeat,"view in publicViews")]/span[contains(.,"{PROJECT_NAME}")]' \
                        ,f'.//li[contains(@ng-repeat,"view in publicViews")]/span[contains(.,"{PROJECT_NAME}")]' \
                        ,'.//span[contains(@ng-click,"searchForResultClick()")]'
    )

    # search results
    print('Searching for results')
    search_result = scraper.navigate(public_views_project.driver \
                            ,EC \
                            ,'.//span[contains(@ng-click,"searchForResultClick()")]' \
                            ,'.//span[contains(@ng-click,"searchForResultClick()")]' \
                            ,'.//span[contains(@ng-click,"setDisplayLimit(2500)")]'
    )

    results_2500 = scraper.navigate(search_result.driver \
                            ,EC \
                            ,'.//span[contains(@ng-click,"setDisplayLimit(2500)")]' \
                            ,'.//span[contains(@ng-click,"setDisplayLimit(2500)")]' \
                            ,'.//div[contains(@style,"padding-top:4px;") and contains(@class, "pull-right template-menu")]'
    )
    
    # export results
    print('Exporting Results')
    export_results = scraper.navigate(results_2500.driver \
                            ,EC \
                            ,'.//div[contains(@style,"padding-top:4px;") and contains(@class, "pull-right template-menu")]' \
                            ,'.//div[contains(@style,"padding-top:4px;") and contains(@class, "pull-right template-menu")]' \
                            ,'.//a[contains(@ng-click,"downloadCSV()")]'
    )

    export_csv = scraper.navigate(export_results.driver \
                            ,EC \
                            ,'.//a[contains(@ng-click,"downloadCSV()")]' \
                            ,'.//a[contains(@ng-click,"downloadCSV()")]' \
                            ,'.//div[contains(@style,"padding-top:4px;") and contains(@class, "pull-right template-menu")]'
    )
    print('File saved')
    sleep(1)
    scraper.init_driver.close()
    scraper.init_driver.quit()

    # upload file
    scraper.upload()
    print('Done Uploading')