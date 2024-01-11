'''
UserContact class for the Webscrapers
'''

class Contact:
    '''
    Class for user contact information and methods for data manipulation
    '''
    # pylint disable=too-many-arguments
    def __init__(self, school: str, sport: str,
                 season: str, name: str, title: str, email: str, phone: str):
        self.school = school
        self.sport = sport
        self.season = season
        self.name = name
        self.title = title
        self.email = email
        self.phone = phone

    def write_to_csv(self, file_name: str):
        '''
        Writes self to the designated csv file
        @param file_name: name of the file to write to
        @return: None
        '''
        with open(file_name, 'a', encoding='utf-8') as file:
            file.write(
                f"{self.school}, {self.sport}, {self.season}"
                f", {self.name}, {self.title}, {self.email}, {self.phone}\n"
            )
        file.close()

    def __str__(self):
        '''
        overridden string method for printing out a contact
        @return: string representation of the contact
        '''
        return (
            f"{self.school}, {self.sport}, {self.season}"
            f", {self.name}, {self.title}, {self.email}, {self.phone}"
        )
