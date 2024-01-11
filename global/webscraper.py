'''
Parent class of each webscraper. Generalized classes are here to reduce code duplication.
'''

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class WebScraper:
    '''
    WebScraper is the parent class of each webscraper.
    '''

    def __init__(self, url: str, fp = 'contacts.csv') -> None:
        self.url = url
        self.driver = self.initialize_driver()
        self.school_links = {}

        self.file_name = fp
        self.debug = False

    def refresh_driver(self) -> None:
        '''
        Closes the driver, waits, and reinitializes a new driver.
        Necessary since the driver will timeout after 2 hours of use.
        @return: None
        '''
        self.driver.quit()
        time.sleep(4)
        self.driver = self.initialize_driver()

    def initialize_driver(self) -> webdriver:
        '''
        Initializes a Selenium webdriver used in fetching the html pages.
        Sets the driver to headless mode, disables any unnecessary add-ons.
        @return: Selenium webdriver object
        '''
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument('window-size=1920x1080')
        driver = webdriver.Chrome(options=chrome_options)
        return driver

    def initialize_file(self) -> None:
        '''
        Initializes the file that the contacts are written to.
        File path is stored in self.file_name
        Has a very broad exception handler since it will create a file if none is found.
        @return: None
        '''
        try:
            with open(self.file_name, 'w', encoding='utf-8') as file:
                file.write('School, Sport, Season, Name, Title, Email, Phone\n')
            file.close()
        # pylint disable=broad-except
        except Exception as exc:
            print(exc)
