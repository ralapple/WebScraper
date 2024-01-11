'''
Parent class of each webscraper. Generalized classes are here to reduce code duplication.
'''


class WebScraperInterface:
    def initialize_driver(self):
        pass
  
    def initialize_file(self):
        pass
