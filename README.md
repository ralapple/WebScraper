# WebScraper Application
Designed to pull contacts off of the MSHSL website without having to navigate and collect by hand.

## Requirements
- This application runs on a few packages that make the functionality possible.
- To install these packages, pip is used.
- Once you have verified that pip is installed, run the command ```make depend```.
- This will attempt to install all of the necessary requirements that are used within this project.

## Running the Program
This program is ran through the terminal. There is a rudimentary user interface that allows the user to select which pages of the website they wish to collect contacts from.

1. Use the terminal to navigate to the directory in which the code is stored.
2. type the command ```make run```.
3. This will begin the program and prompt for more user input.
4. The program will prompt the user for a starting page, this is a number between 1 and 14 of which page you would like to start extracting contacts from.
5. The next prompt will be the end page, this is also a value between 1 and 14 and this is the last page you would like included in the extraction (if one page is wanted, both values will be the same).
6. The program will run and when complete, a contacts.csv file and contacts.xslx file will be present in the directory.

## Notes
- Nothing should be placed in the /resource folder to ensure that the final contact file is correct
- The program will take time, when tested, it took about 1 hour and 45 minutes to complete. This is also dependent on network speeds and the computer that it runs on.
- The program was last tested 1/4/24, changes to the MSHSL website may affect performance and functionality since it is a dynamic website.

### Contact
- Developed by Raymond Lyon

##### Disclaimer
This software was developed with the intent to safely extract contacts from the MSHSL website without having to manually navigate and record each contact. There were no malicious acts intended in the creation of this software. 
