'''
Web scraper for the state of Wisconsin schools
'''


sys.path.insert(1, 'scrapers/global_')
from webscraper import WebScraper
from contact import Contact


import time
import threading
import os
import sys
from bs4 import BeautifulSoup as bs
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options



class WiWebScrape(WebScraper):
    '''
    instance of a webscrape object used for collecting contact information
    '''
    def __init__(self, url: str, fp = 'contacts.csv') -> None:
        self: WebScraper.__init__(self, url, fp)
        self.url = url
        self.driver = self.initialize_driver()
        self.school_links = {}

        self.file_name = fp
        self.debug = False

    def set_page_select_length(self,url: str, length: int) -> None:
        '''
        Sets the page length drop down on the html page
        Possible values are 10, 25, 50, 100, -1
        @param url: url of the page to set the page length
        @param length: value of the page length
        @return: None
        '''
        self.driver.get(url)
        select = Select(self.driver.find_element(By.NAME,'tblSchools_length'))
        select.select_by_value(str(length))

    def get_school_links(self, page_distinction: str) -> None:
        '''
        Retrieves the school names and thier corresponding links from the school directory page.
        Directly updates the school_links dictionary.
        @param page_distinction: letter to distinguish the page (A, B, C, etc.)
        @return: None
        '''
        url = self.page_query_builder(self.url, page_distinction)
        self.set_page_select_length(url, -1)
        page = self.convert_page(url)

        # table of schools
        table = page.find('tbody')
        if table:
            # find all rows in the table
            rows = table.find_all('tr', role='row')
            print(len(rows))
            for row in rows:
                school_info_container = row.find('a')
                school_name = (school_info_container.find('h5').text).strip().replace(',', '-')
                school_link = school_info_container.get('href')
                self.school_links[school_name] = school_link

            if self.debug:
                for school, link in self.school_links.items():
                    print(f"School: {school}, Link: {link}")


    def get_sport_links(self, school_name: str, school_url: str) -> str:
        '''
        Accesses a school page, navigates to the coaches tab, and grabs the components.
        Most heavy lifting of the program.
        @param school_name: name of the school to be passed into the UserContact object
        @param school_url: url of the school to be scraped
        @return: None
        '''
        self.driver.get(self.url + school_url)
        # Wait for the tab to be clickable
        coaches_tab = WebDriverWait(self.driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//a[@href="#Coaches"]'))
        )
        coaches_tab.click()
        # Wait for the page to load (you can adjust the wait time accordingly)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//table[@id="tblCoachList"]'))
        )
        coaches_table = bs(self.driver.page_source, 'html.parser').find(
            'table', {'id': 'tblCoachList'})

        sport_season_dict = self.get_sport_seasons(self.url + school_url)

        if coaches_table:
            rows = coaches_table.find_all('tr', role='row')[1:]
            for row in rows:
                # first container is sport name
                # second container is personell name and link to their profile
                # third link is position
                internal_containers = (row.find_all(
                    'td', class_='gridDataFont dataTableWrap align-middle'))
                sport = (
                    internal_containers[0].find('label', class_='formText'
                                                ).text).strip().replace(',', '-')

                name_link = internal_containers[1].find('a').get('href')
                name, email, phone = self.get_contact_information(name_link)

                title = (
                    internal_containers[2].find(
                        'label', class_='formText').text).strip().replace(',', '-')

                # check for sport season
                if sport in sport_season_dict:
                    season = sport_season_dict.get(sport)
                else:
                    season = 'N/A'

                Contact(
                    school_name, sport, season, name, title, email, phone
                    ).write_to_csv(self.file_name)

    def get_sport_seasons(self, url: str) -> dict:
        '''
        Creates a dictionary of the sports and their corresponding seasons.
        @param sport_url: url of the sport page
        @return: dictionary of the sports and their corresponding seasons
        '''

        seasons = {}

        self.driver.get(url)

        sports_tab = WebDriverWait(self.driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//a[@href="#Teams"]'))
        )

        sports_tab.click()

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//table[@id="tblTeamList"]'))
        )

        sports_page = bs(self.driver.page_source, 'html.parser')
        # since there are two tbodys within the html, we need to find the correct one
        team_div = sports_page.find('div', id='TeamList')
        sports_table = team_div.find('tbody')

        if sports_table:
            rows = sports_table.find_all('tr', role='row')
            for row in rows:
                sport_name = row.find('span').text.strip().replace(',', '-')
                season = row.find('label', class_='formText').text.strip().replace(',', '-')
                # populate the dictionary
                seasons[sport_name] = season
        return seasons

    def get_contact_information(self, contact_profile_page: str) -> tuple:
        '''
        Scrapes the contact information off of the html contact profile page.
        @param contact_profile_page: url of the contact profile page
        @return: tuple of the contact information
        '''
        url = self.url + contact_profile_page
        page = self.convert_page(url, 0.5)

        rows = page.find_all('div', class_='row')

        name = rows[0].find_all('label')
        name = (name[1].text.strip() + ' ' + name[2].text.strip())
        if ',' in name:
            name = name.split(',')[1].strip() + ' ' + name.split(',')[0].strip()
            name += '(edited: may be of form "last/first"))'
        email = rows[0].find('b').text.strip()
        phone = rows[2].find_all('label')[1].text.strip()
        return name, email, phone


    def instance_handler(self, page_letter: str) -> None:
        '''
        Handles the single instance of the webscrape object.
        @param page_letter: letter to distinguish the page (A, B, C, etc.)
        @return: None
        '''
        start_time = time.time()
        self.initialize_file()
        self.get_school_links(page_letter)
        for school, link in self.school_links.items():
            if (time.time() - start_time) > 3600:
                self.refresh_driver()
                start_time = time.time()
            self.get_sport_links(school, link)

    def page_query_builder(self, url: str, page_letter: str) -> str:
        '''
        Builds the URL of the page to be scraped.
        Works for the original pagenation of the site.
        @param url: url of the main page
        @param page_letter: letter to distinguish the page (A, B, C, etc.)
        @return: url of the page to be scraped
        '''
        return url + f"Directory/School/List?Letter={page_letter}"

    def convert_page(self, url: str, wait_time = 4) -> bs:
        '''
        Requests a page and then converts it to a BeautifulSoup object
        @param url: url of the page to be requested
        @param wait_time: time to wait before converting the page
        @return: BeautifulSoup object of the requested page
        '''
        self.driver.get(url)
        time.sleep(wait_time)
        page = self.driver.page_source
        return bs(page, 'html.parser')

def stitch_contact_files(folder_path: str) -> None:
    '''
    Navigates the resource folder and stitches all the contact files into one file.
    @param folder_path: the path to the folder where the contact files are located
    @return: none
    '''

    csv_files = [file for file in os.listdir(folder_path) if file.endswith('.csv')]
    csv_files = sorted(csv_files, key=lambda x: (x.split('_')[1]).split('.')[0])

    if not csv_files:
        print("No files to stitch")
        return


    combined_csv = pd.DataFrame()
    first_file = True
    for file in csv_files:
        print(file)
        current_file = pd.read_csv(os.path.join(folder_path, file))

        if not first_file:
            current_file = current_file[1:]

        combined_csv = pd.concat([combined_csv, current_file])

        first_file = False

    combined_csv.to_csv('contacts.csv', index=False, encoding='utf-8')

    directory = os.listdir(folder_path)
    for file in directory:
        if file.endswith('.csv'):
            os.remove(os.path.join(folder_path, file))

    data = pd.read_csv('contacts.csv')
    data.to_excel('contacts.xlsx', index=False)
    print("All contacts located in contacts.csv and exported to excel file")

def multi_handle(start_page = 1, end_page = 1) -> None:
    '''
    Handler for efficiently scraping the site with multiple threads.
    Cuts the runtime down by a factor of 10.
    Default url is the MSLSH website
    Start page and end page can only be values 1 - 14
    @param start_page: int: the page number to start on
    @param end_page: int: the page number to end on includes this page in the scrape
    @return: none
    '''
    # catch pages out of bounds
    start_page = max(1, min(start_page, 14))
    end_page = max(1, min(end_page, 26))

    reaminder = (end_page - start_page + 1) % 10
    num_tens = (end_page - start_page + 1) // 10

    page_destinction = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
    index = 0
    #pylint disable=unused-variable
    for j in range(num_tens):
        running_threads = []
        for i in range(10):
            scrape = WiWebScrape('https://schools.wiaawi.org/',
                                'scrapers/wi/resource/page_' + str(page_destinction[index]) + '.csv')
            thread = threading.Thread(
                target=scrape.instance_handler, args=(page_destinction[index],))
            running_threads.append(thread)
            thread.start()
            index += 1

        for thread in running_threads:
            thread.join()

    running_threads = []
    #Pylint disable=unused-variable
    for remain in range(reaminder):
        scrape = WiWebScrape('https://schools.wiaawi.org/',
                            'scrapers/wi/resource/page_' + str(page_destinction[index]) + '.csv')
        thread = threading.Thread(target=scrape.instance_handler, args=(page_destinction[index],))
        running_threads.append(thread)
        thread.start()
        index += 1

    for thread in running_threads:
        thread.join()
    stitch_contact_files('scrapers/wi/resource')

if __name__ == '__main__':
    multi_handle(1,26)
