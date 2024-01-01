'''
MHSLS Scraping software, extracts the contact information from the MSHSL website for each school, sport, and season
Developed by: Lyon Coding LLC
'''

# import necessary libraries
import time
from bs4 import BeautifulSoup as bs

# Selenium over requests since it loads all the dynamic components of the site
from selenium import webdriver

# Data structure for storing contact information
class Contact:
    '''
    A class to represent contacts
    Each member is stored as a contact object for easy data handling
    '''
    def __init__(self, school, sport, season, name, position, title, phone_number, email):
        self.school = school
        self.sport = sport
        self.season = season
        self.name = name
        self.position = position
        self.title = title
        self.phone_number = phone_number
        self.email = email

    def __str__(self):
        return f"{self.school} - {self.sport} - {self.season} - {self.name} - {self.position} - {self.title} - {self.phone_number} - {self.email}"

class WebScraper:
    def __init__(self, origin_url) -> None:
        self.contacts = []
        self.origin_url = origin_url

        self.school_links = {}

        self.school_count = 0
        self.total_sports = 0

        self.driver = webdriver.Chrome()


    def extract_contacts_from_sport_page(self, page, school, season, sport) -> None:
        '''
        Takes a list of grid items and extracts the needed information
        '''

        team_info = page.find('div', class_='heading-echo-wrapper')

        # pull the team info
        if team_info:
            team_name = (team_info.find('h1').text).strip()
        else:
            team_name = 'no team name found'

        # locate the html container that stores the personel info
        container = page.find(id='react-team-personnel')

        lst = container.find_all("div", class_='grid__item')

        if lst is None:
            print("no grid items found")
            return None

        # iterate each person with contacts
        for grid_item in lst:
            # reset variables
            email = 'no email found'
            phone_number = 'no phone number found'

            # extract name and position
            name = grid_item.find("div", class_='team-personel-title').find("strong").text
            position = grid_item.find("div", class_='team-personel-position').text

            # iterate the contacts of each person
            contacts = grid_item.find_all("div", class_='grid-contact')
            if contacts:
                for contact in contacts:
                    if contact.find('span'):
                        phone_number = contact.find('span').text

                    if contact.find('a'):
                        email = contact.find('a').get('href')
                        email = email.split(':')[1]

            self.contacts.append(Contact(school, sport, season, name, position, "need_to_fill", phone_number, email))

    def extract_sports_links_from_school(self, page: bs, school_name) -> None:
        '''
        Uses the page of a school to extract the sport name, season, and link
        @param page: the page of a school in bs4 format
        @return: none
        '''

        team_list_container = page.find('div', id = 'react-school-team-list')

        if team_list_container:
            seasons = team_list_container.find_all('div', class_ = 'container gutter region--space-md')
            for season in seasons:
                season_name = season.find('h3').text
                season_activites = season.find_all('span', class_ = 'wrapper-link')
                for activity in season_activites:
                    activity_name = activity.find('a').text
                    activity_link = activity.find('a').get('href')
                    self.extract_contacts_from_sport_page(self.quick_convert_page(self.origin_url + activity_link), school_name, season_name, activity_name)
                    self.total_sports += 1


    def extract_school_names_and_links(self) -> None:
        '''
        Takes a page and populates the dictionary with school names as the keys and their respective links as the value
        @param page: the page of the schools list in bs4 format
        '''
        # Calculate number of pages

        # Iterate each page and extract schools with links

        current_page = 0

        while current_page == 0:
            current_url = page_query_builder(self.origin_url + "/schools", current_page)

            page = self.convert_page(current_url)
            temp = page.find_all('div', class_='views-row')[:-1]
            if temp == []:
                break
            for school in temp:
                self.school_links[(school.find('a').text).strip()] = school.find('a').get('href')
                self.school_count += 1
            print(f"Schools counted: {len(self.school_links)}")
            current_page += 1
        # for key, value in self.school_links.items():
        #     print(f"School: {key}, Link: {value}")

    def perform_scrape(self) -> None:
        '''
        Handles the logistics of scraping the site
        @return: none
        '''

        # populates the dictionary of school names and their links for later use
        self.extract_school_names_and_links()

        # iterate each school and extract the contacts
        for school, link in self.school_links.items():
            school_page = self.convert_page(self.origin_url + link)
            self.extract_sports_links_from_school(school_page, school)

        self.write_contacts_to_file()
        self.print_metrics()
        self.close()
        

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

    def write_contacts_to_file(self, filename='contacts.csv') -> None:
        '''
        Writes the contacts to a csv file
        '''
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('School, Sport, Season, Name, Position, Title, Phone Number, Email\n')
            for contact in self.contacts:
                f.write(f"{contact.school}, {contact.sport}, {contact.season}, {contact.name}, {contact.position}, {contact.title}, {contact.phone_number}, {contact.email}\n")

    def close(self) -> None:
        '''
        Closes the driver
        '''
        self.driver.quit()

    
    def convert_page(self, url) -> bs:
        self.driver.get(url)
    
        self.driver.implicitly_wait(3)
        time.sleep(5)

        page_source = self.driver.page_source
        soup = bs(page_source, 'html.parser')
        return soup
    

    def quick_convert_page(self,url) -> bs:
        self.driver.get(url)
        page_source = self.driver.page_source
        soup = bs(page_source, 'html.parser')
        return soup


# UNIVERSAL FUNCTIONS
def page_query_builder(url, page_num) -> str:
    '''
    Builds the url for the different pages
    '''
    return url + f"?page={page_num}"

def test_write():
    with open('contacts.csv', 'w', encoding='utf-8') as f:
            f.write('School, Sport, Season, Name, Position, Title, Phone Number, Email\n')


if __name__ == "__main__":
    # test_write()
    scrape = WebScraper('https://www.mshsl.org')
    scrape.perform_scrape()

