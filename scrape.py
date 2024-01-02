'''
MHSLS Scraping software, extracts the contact information from the MSHSL website for each school, sport, and season
Developed by: Raymond Lyon
'''

# import necessary libraries
import time
from bs4 import BeautifulSoup as bs

# Selenium over requests since it loads all the dynamic components of the site
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# Data structure for storing contact information
class Contact:
    '''
    A class to represent contacts
    Each member is stored as a contact object for easy data handling
    '''
    def __init__(self, school, sport, season, name, position, phone_number, email):
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
    def __init__(self, origin_url) -> None:
        self.contacts = []
        self.origin_url = origin_url
        self.school_links = {}
        self.school_count = 0
        self.total_sports = 0

        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--disable-extensions")
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.contacts_filepath = 'contacts.csv'


    def extract_contacts_from_sport_page(self, link, school, season, sport) -> None:
        '''
        Takes a list of grid items and extracts the needed information
        @param page: the page of a sport in bs4 format
        @param school: the school name
        @param season: the season name
        @param sport: the sport name
        @return: none
        '''

        # locate the html container that stores the personel info
        page = self.convert_page(link, 1)

        container = page.find(id='react-team-personnel')
        grid_item_list = container.find_all("div", class_='grid__item')
        print(f"School: {school}, Sport: {sport}, Season: {season}, Number of Contacts: {len(grid_item_list)}")

        if len(grid_item_list) == 0:
            print("Retrying with longer wait time")
            page = self.convert_page(link, 2)
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

    def extract_sports_links_from_school(self, link: str, school_name) -> None:
        '''
        Uses the page of a school to extract the sport name, season, and link
        @param page: the page of a school in bs4 format
        @return: none
        '''
        # find the container that stores each of the sports

        page = self.convert_page(link, 2)
        team_list_container = page.find('div', id = 'react-school-team-list')
        
        if team_list_container:
            seasons = team_list_container.find_all('div', class_ = 'container gutter region--space-md')
            print(f"School: {school_name}, Number of Seasons: {len(seasons)}")

            # if the dynamic content is not loaded, retry with a longer wait time
            if seasons == []:
                print("Retrying with longer wait time")
                page = self.convert_page(link, 6)
                team_list_container = page.find('div', id = 'react-school-team-list')
                seasons = team_list_container.find_all('div', class_ = 'container gutter region--space-md')
                print(f"School: {school_name}, Number of Seasons: {len(seasons)}")

            # iterate each season capturing the season name and the activities
            for season in seasons:
                season_name = season.find('h3').text
                season_activites = season.find_all('span', class_ = 'wrapper-link')
                # print(f"Number of Activities: {len(season_activites)}")
                for activity in season_activites:
                    activity_name = self.replace_comma_in_sport(activity.find('a').text)
                    activity_link = activity.find('a').get('href')
                    self.extract_contacts_from_sport_page((self.origin_url + activity_link), school_name, season_name, activity_name)
                    self.total_sports += 1



    def extract_school_names_and_links(self, start_page = 0) -> None:
        '''
        Takes a page and populates the dictionary with school names as the keys and their respective links as the value
        @param page: the page of the schools list in bs4 format
        '''
        current_page = start_page
        print("Extracting School Names and Links")
        while True:
            current_url = page_query_builder(self.origin_url + "/schools", current_page)

            page = self.convert_page(current_url, 1)
            page_content = page.find_all('div', class_='views-row')[:-1]
            if page_content == []:
                break
            for school in page_content:
                self.school_links[(school.find('a').text).strip()] = school.find('a').get('href')
                self.school_count += 1
            current_page += 1

        for school, link in self.school_links.items():
            print(f"School: {school}, Link: {link}")


        print("total school count: ", self.school_count)

    def perform_scrape(self) -> None:
        '''
        Handles the logistics of scraping the site
        @return: none
        '''
        start_time = time.time()
        self.initialize_file()

        # populates the dictionary of school names and their links for later use
        self.extract_school_names_and_links(0)

        # iterate each school and extract the contacts
        for school, link in self.school_links.items():
            if start_time > 3600:
                self.driver.quit()
                self.driver = webdriver.Chrome(options=self.chrome_options)
            self.extract_sports_links_from_school((self.origin_url + link), school)

        self.print_metrics()
        self.close()
        print(f"Time Elapsed: {time.time() - start_time} seconds")

    def print_metrics(self) -> None:
        '''
        Prints the metrics of the scrape
        '''
        print(f"Number of Schools: {self.school_count}")
        print(f"Number of Sports: {self.total_sports}")
        print(f"Number of Contacts: {len(self.contacts)}")

    def list_contacts(self) -> None:
        '''
        Prints the contacts that were obtained
        '''
        for contact in self.contacts:
            print(contact)

    def initialize_file(self) -> None:
        '''
        Initializes the file with the headers of the csv file
        makes sure that the file is empty before writing.
        '''
        with open(self.contacts_filepath, 'w', encoding='utf-8') as f:
            f.write('School, Sport, Season, Name, Position, Phone Number, Email\n')
        f.close()


    def write_contact_to_file(self, contact) -> None:
        '''
        Writes a single contact to the file. Used to write contacts as they are scraped.
        '''
        with open(self.contacts_filepath, 'a', encoding='utf-8') as f:
            f.write(f"{contact.school}, {contact.sport}, {contact.season}, {contact.name}, {contact.position}, {contact.phone_number}, {contact.email}\n")
        f.close()

    def close(self) -> None:
        '''
        Closes the selenium driver.
        '''
        self.driver.quit()

    def convert_page(self, url, wait_time = 4) -> bs:
        '''
        Converts the page to bs4 format.
        '''
        self.driver.get(url)
        time.sleep(wait_time)
        page_source = self.driver.page_source
        soup = bs(page_source, 'html.parser')
        return soup
    
    def replace_comma_in_sport(self, sport) -> str:
        '''
        Replaces the comma in the sport name with a dash
        '''
        return sport.replace(',', '-')

# UNIVERSAL FUNCTIONS
def page_query_builder(url, page_num) -> str:
    '''
    Builds the url for the different pages
    '''
    return url + f"?page={page_num}"

if __name__ == "__main__":
    scrape = WebScraper('https://www.mshsl.org')
    scrape.perform_scrape()
