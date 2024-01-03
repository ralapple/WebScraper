'''
MHSLS Scraping software, extracts the contact information from the MSHSL website for each school, sport, and season
Developed by: Raymond Lyon
'''

# import necessary libraries
import time
import os
import threading
from bs4 import BeautifulSoup as bs

# Selenium over requests since it loads all the dynamic components of the site
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Data structure for storing contact information
class Contact:
    '''
    A class to represent contacts
    Each member is stored as a contact object for easy data handling
    '''
    def __init__(self, school: str, sport: str, season: str, name: str, position: str, phone_number: str, email: str):
        self.school = school
        self.sport = sport
        self.season = season
        self.name = name
        self.position = position
        self.phone_number = phone_number
        self.email = email

    def __str__(self):
        return f"{self.school} - {self.sport} - {self.season} - {self.name} - {self.position} - {self.phone_number} - {self.email}"

class WebScraper:
    '''
    Instance of the web scraper
    Purpose: to scrape the MSHSL website for contact information
    '''
    def __init__(self, origin_url: str, file_name: str) -> None:
        # Object attributes
        self.contacts = []
        self.origin_url = origin_url
        self.school_links = {}
        self.school_count = 0
        self.total_sports = 0
        self.debug = False
        
        # Selenium driver setup
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--disable-extensions")
        self.driver = webdriver.Chrome(options=self.chrome_options)

        # File handling
        self.contacts_filepath = file_name + '.csv'


    def extract_contacts(self, sport_page_link: str, school: str, season: str, sport: str) -> None:
        '''
        Takes a list of grid items and extracts the needed information
        @param page: the page of a sport in bs4 format
        @param school: the school name
        @param season: the season name
        @param sport: the sport name
        @return: none
        '''

        # locate the html container that stores the personel info
        page = self.convert_page(sport_page_link, 2)

        container = page.find(id='react-team-personnel')
        grid_item_list = container.find_all("div", class_='grid__item')
        print(f"School: {school}, Sport: {sport}, Season: {season}, Number of Contacts: {len(grid_item_list)}")

        # if the dynamic content is not loaded, retry with a longer wait time
        if len(grid_item_list) == 0:
            print("Retrying with longer wait time")
            page = self.convert_page(sport_page_link, 4)
            container = page.find(id='react-team-personnel')
            grid_item_list = container.find_all("div", class_='grid__item')
            print(f"School: {school}, Sport: {sport}, Season: {season}, Number of Contacts: {len(grid_item_list)}")
        

        # iterate each person with contacts
        for grid_item in grid_item_list:
            # reset variables
            email = 'no email listed'
            phone_number = 'no phone number listed'

            # extract name and position
            name = grid_item.find("div", class_='team-personel-title').find("strong").text
            position = grid_item.find("div", class_='team-personel-position').text

            # iterate the contacts of each person
            contacts = grid_item.find_all("div", class_='grid-contact')

            for contact in contacts:
                if contact.find('span'):
                    phone_number = contact.find('span').text
                    if phone_number == 'xxx-xxx-xxxx':
                        phone_number = 'no phone number listed'
                if contact.find('a'):
                    email = contact.find('a').get('href')
                    email = email.split(':')[1]

            contact = Contact(school, sport, season, name, position, phone_number, email)
            # update the contacts list
            self.contacts.append(contact)
            # write the contact to the file as it is scraped
            self.write_contact_to_file(contact)

    def extract_sports(self, school_link: str, school_name: str) -> None:
        '''
        Uses the page of a school to extract the sport name, season, and link
        @param page: the page of a school in bs4 format
        @return: none
        '''
        # find the container that stores each of the sports

        page = self.convert_page(school_link, 5)
        team_list_container = page.find('div', id = 'react-school-team-list')
        
        if team_list_container:
            seasons = team_list_container.find_all('div', class_ = 'container gutter region--space-md')
            print(f"School: {school_name}, Number of Seasons: {len(seasons)}")

            # if the dynamic content is not loaded, retry with a longer wait time
            if seasons == []:
                print("Retrying with longer wait time")
                page = self.convert_page(school_link, 10)
                team_list_container = page.find('div', id = 'react-school-team-list')
                seasons = team_list_container.find_all('div', class_ = 'container gutter region--space-md')
                print(f"School: {school_name}, Number of Seasons: {len(seasons)}")

            # iterate each season capturing the season name and the activities
            for season in seasons:
                season_name = season.find('h3').text
                season_activites = season.find_all('span', class_ = 'wrapper-link')
                # print(f"Number of Activities: {len(season_activites)}")
                for activity in season_activites:
                    activity_name = (activity.find('a').text).replace(',', '-')
                    activity_link = activity.find('a').get('href')
                    self.extract_contacts((self.origin_url + activity_link), school_name, season_name, activity_name)
                    self.total_sports += 1



    def extract_schools(self, page_number=0) -> None:
        '''
        Uses the origin url to formulate a url for the page that is wanted to scrape, extracts the school names and links from the pages.
        @param page_number: the page number to scrape
        '''
        print("Extracting School Names and Links of page " + str(page_number))

        current_url = page_query_builder(self.origin_url + "/schools", page_number)

        page = self.convert_page(current_url, 1)
        page_content = page.find_all('div', class_='views-row')[:-1]

        # iterates each school that was on the page and extracts the name and link
        for school in page_content:
            self.school_links[(school.find('a').text).strip()] = school.find('a').get('href')

            # counts the number of schools
            self.school_count += 1

        if self.debug:
            for school, link in self.school_links.items():
                print(f"School: {school}, Link: {link}")


    def print_metrics(self) -> None:
        '''
        Prints the metrics of the scrape after completion to show the user the results.
        @return: none
        '''
        print(f"Number of Schools: {self.school_count}")
        print(f"Number of Sports: {self.total_sports}")
        print(f"Number of Contacts: {len(self.contacts)}")

    # FILE HANDLING FUNCTIONS
    def initialize_file(self) -> None:
        '''
        Clears out the file path and writes the headers to the file.
        @return: none
        '''
        with open(self.contacts_filepath, 'w', encoding='utf-8') as f:
            f.write('School, Sport, Season, Name, Position, Phone Number, Email\n')
        f.close()

    def write_contact_to_file(self, contact: Contact) -> None:
        '''
        Writes a single contact to the file. Used to write contacts as they are scraped.
        @param contact: the contact object to write to the file
        @return: none
        '''
        with open(self.contacts_filepath, 'a', encoding='utf-8') as f:
            f.write(f"{contact.school}, {contact.sport}, {contact.season}, {contact.name}, {contact.position}, {contact.phone_number}, {contact.email}\n")
        f.close()

    def close(self) -> None:
        '''
        Closes the selenium driver for safe exit
        @return: none
        '''
        self.driver.quit()

    def convert_page(self, url: str, wait_time = 4) -> bs:
        '''
        Converts the page to bs4 format for easy html extraction
        @param url: the url to convert
        @param wait_time: the time to wait for the page to load: default is 4 seconds for the dynamic content to load.
        @return: the page in bs4 format
        '''
        self.driver.get(url)
        time.sleep(wait_time)
        page_source = self.driver.page_source
        soup = bs(page_source, 'html.parser')
        return soup
    
    def scrape_handler(self, page_number: int) -> None:
        '''
        Handles the logistics of scraping the site, calls the necessary functions to scrape the site
        @param page_number: the page number to scrape
        @return: none
        '''
        start_time = time.time()

        # clear out the file and write the headers
        self.initialize_file()

        # populates the dictionary of school names and their links for later use
        self.extract_schools(page_number)

        # iterate each school and extract the contacts
        for school, link in self.school_links.items():

            # selenium driver closes after 2 hours so this maintains a fresh connection
            if start_time > 3600:
                self.driver.quit()
                print("Restarting Driver for new connection")
                time.sleep(10)
                self.driver = webdriver.Chrome(options=self.chrome_options)
            self.extract_sports((self.origin_url + link), school)

        # Safely close the object
        self.close()

        if self.debug:
            print(f"Time Elapsed: {time.time() - start_time} seconds")

    
# UNIVERSAL FUNCTIONS
def page_query_builder(url, page_num: int) -> str:
    '''
    Builds the url for the different pages

    '''
    return url + f"?page={page_num}"

def stitch_contact_files(folder_path: str) -> None:
    '''
    Navigates the resource folder and stitches all the contact files into one file.
    @param folder_path: the path to the folder where the contact files are located
    @return: none
    '''
    files = os.listdir(folder_path)

    with open('contacts.csv', 'w', encoding='utf-8') as f:
        f.write('School, Sport, Season, Name, Position, Phone Number, Email\n')
        for file in files:
            if os.path.isfile(file):
                with open(file, 'r', encoding='utf-8') as f2:
                    f.write(f2.read())
                f2.close()

    f.close()
    print("All contacts located in contacts.csv")

def multi_handle(start_page = 1, end_page = 1) -> None:
    '''
    Handler for efficiently scraping the site with multiple threads.
    Cuts the runtime down by a factor of 10.
    Default url is the MSLSH website
    @param start_page: int: the page number to start on
    @param end_page: int: the page number to end on includes this page in the scrape
    @return: none
    '''

    running_threads = []
    for i in range(start_page, end_page + 1):
        scrape = WebScraper('https://www.mshsl.org', './resource/page_' + str(i))
        thread = threading.Thread(target=scrape.scrape_handler, args=(i-1,))
        running_threads.append(thread)
        thread.start()

    for thread in running_threads:
        thread.join()

    stitch_contact_files('./resource')

def user_interface():
    '''
    Handles the user interface for the scraper.
    @return: none
    '''
    print("Welcome to the MSHSL Web Scraper")
    print("Please enter the page number you would like to start on: ")
    start_page = int(input())
    print("Please enter the page number you would like to end on: ")
    end_page = int(input())
    multi_handle(start_page, end_page)

if __name__ == "__main__":
    user_interface()
