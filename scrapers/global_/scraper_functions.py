'''
General functions for scraping data from the web, writing to files, and other
methods that are reused throughout each scraper.
'''

import os
import pandas as pd


def stitch_contact_files(folder_path: str) -> None:
    '''
    Navigates the resource folder and stitches all the contact files into one file.
    @param folder_path: the path to the folder where the contact files are located
    @return: none
    '''

    csv_files = [file for file in os.listdir(folder_path) if file.endswith('.csv')]
    csv_files = sorted(csv_files, key=lambda x: ord((x.split('_')[1]).split('.')[0]))

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
