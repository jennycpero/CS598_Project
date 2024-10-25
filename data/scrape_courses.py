from selenium import webdriver
import chromedriver_autoinstaller
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import copy
import re

url = "https://webapps.wichita.edu/CourseSearch/CourseSearch"

driver = webdriver.Firefox()
driver.get(url)

selectTerm = Select(driver.find_element(By.ID, 'MainContent_semesterDDL'))
selectTerm.select_by_visible_text("Fall 2024")

subjects = driver.find_element(By.XPATH, "/html/body/form/div[3]/div[2]/div/div[1]/div[2]/div[1]/select")
driver.execute_script("arguments[0].click();", subjects)
all_subjects = driver.find_element(By.ID, "MainContent_SubjectCbl_0")
all_subjects.click()

try:
    element_present = EC.presence_of_element_located((By.XPATH, "/html/body/form/div[3]/div[2]/div/div[2]/div[5]/table[1]/tbody/tr[1]/td"))
    WebDriverWait(driver, 5).until(element_present)
except TimeoutException:
    print("Timed out waiting for page to load")

html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

headerTables = soup.find_all('table', {"class": "courseHeaderTable"})

tables_with_data = []

for i in range(len(headerTables)):
    # Start with the current main table
    current_table = headerTables[i]
    
    # Initialize a string to hold the HTML content
    combined_html = str(current_table)  # Start with the HTML of the main table
    
    # Check if there's a next main table
    if i + 1 < len(headerTables):
        next_table = headerTables[i + 1]
    else:
        next_table = None  # If no more tables, capture all remaining siblings
    
    # Collect all data between current_table and the next table
    sibling = current_table.next_sibling
    while sibling != next_table:
        if sibling and sibling.name:  # Check if it's a valid tag and not just a newline or text node
            if sibling.name == 'table':
                # Append the HTML part of the sibling table
                combined_html += str(sibling)  # Concatenate the HTML of the sibling table
            sibling = sibling.next_sibling
        else:
            sibling = sibling.next_sibling

    # Add the combined HTML (main table + associated elements) to the list
    tables_with_data.append(combined_html)

driver.quit()

column_names = ['Title', 'Description', 'Department', 'Levels', 'Class Quota', 'Waitlist Maximum', 'Instructor', 'CRN', 'Time', 'Days', 'Date', 'Where', 'Course Type', 'Method', 'Credit Hours']

def extract_table_data(soup):
    rows_data = []

    # Find the table
    data_row = soup.find('tr', class_='courseSectionRow2_2')
    
    if data_row:
        # Extract text from <td> elements in the row
        row_data = [td.get_text(strip=True) for td in data_row.find_all('td')]
        
    return row_data

def extract_specific_data(soup):
    data = {}

    # Title
    title_data = soup.find('tr', class_='courseHeaderRow')
    if title_data:
        title_td = [td.get_text(strip=True) for td in title_data.find_all('td')]
        data['Title'] = str(title_td)
    else:
        print("Title data not found.")  # Debug print
        data['Title'] = "Not Found"

    # Description
    desc_data = soup.find('tr', class_='descDiv')
    if desc_data:
        desc_td = [td.get_text(strip=True) for td in desc_data.find_all('td')]
        data['Description'] = str(desc_td)
    else:
        print("Description data not found.")  # Debug print
        data['Description'] = "Not Found"

    # Department
    department_data = soup.find(text=lambda text: text and "Department:" in text)
    if department_data:
        department_td = department_data.find_parent('td')
        if department_td:
            #print(f"Found Department TD: {department_td}")  # Debug print
            department_parts = re.split(r':\s*', department_td.get_text(strip=True), maxsplit=1)
            data['Department'] = str(department_parts[1])
        else:
            print("Department TD not found.")  # Debug print
            data['Department'] = "Not Found"
    else:
        print("Department data not found.")  # Debug print
        data['Department'] = "Not Found"

    #Level
    level_data = soup.find(text=lambda text: text and "Levels:" in text)
    if level_data:
        level_td = level_data.find_parent('td')
        if level_td:
            #print(f"Found Department TD: {department_td}")  # Debug print
            level_parts = re.split(r':\s*', level_td.get_text(strip=True), maxsplit=1)
            data['Levels'] = str(level_parts[1])
        else:
            print("Levels TD not found.")  # Debug print
            data['Levels'] = "Not Found"
    else:
        print("Levels data not found.")  # Debug print
        data['Levels'] = "Not Found"

    # Class Quota
    quota_data = soup.find(text=lambda text: text and "Class Quota" in text)
    if quota_data:
        quota_td = quota_data.find_parent('td')
        if quota_td:
            #print(f"Found Seats Available TD: {seats_td}")  # Debug print
            quota_parts = re.split(r':\s*', quota_td.get_text(strip=True), maxsplit=1)
            data['Class Quota'] = str(quota_parts[1])
        else:
            print("Seats TD not found.")  # Debug print
            data['Class Quota'] = "Not Found"
    else:
        print("Seats data not found.")  # Debug print
        data['Class Quota'] = "Not Found"

    #Waitlist Maximum
    waitmax_data = soup.find(text=lambda text: text and "Waitlist Maximum:" in text)
    if waitmax_data:
        waitmax_td = waitmax_data.find_parent('td')
        if waitmax_td:
            #print(f"Found Instructor TD: {instructor_td}")  # Debug print
            waitmax_parts = re.split(r':\s*', waitmax_td.get_text(strip=True), maxsplit=1)
            data['Waitlist Maximum'] = str(waitmax_parts[1])
        else:
            print("Waitlist TD not found.")  # Debug print
            data['Waitlist Maximum'] = "Not Found"
    else:
        print("Waitlist data not found.")  # Debug print
        data['Waitlist Maximum'] = "Not Found"

    # Instructor
    instructor_data = soup.find(text=lambda text: text and "Instructor:" in text)
    if instructor_data:
        instructor_td = instructor_data.find_parent('td')
        if instructor_td:
            #print(f"Found Instructor TD: {instructor_td}")  # Debug print
            instructor_parts = re.split(r':\s*', instructor_td.get_text(strip=True), maxsplit=1)
            data['Instructor'] = str(instructor_parts[1])
        else:
            print("Instructor TD not found.")  # Debug print
            data['Instructor'] = "Not Found"
    else:
        print("Instructor data not found.")  # Debug print
        data['Instructor'] = "Not Found"

    return data

# Initialize a list to hold all extracted data
all_data = []

# Iterate through each combined HTML block in tables_with_data
for index, combined_html in enumerate(tables_with_data):
    print(f"Processing Set {index + 1} HTML")  # Debug: print the set number
    soup = BeautifulSoup(combined_html, 'html.parser')
    
     # Extract multiple pieces of data
    specific_data = extract_specific_data(soup)

    table_data = extract_table_data(soup)

    # Combine specific data with table data
    combined_row = [
        specific_data.get('Title', 'Not Found'),
        specific_data.get('Description', 'Not Found'),
        specific_data.get('Department', 'Not Found'),
        specific_data.get('Levels', 'Not Found'),
        specific_data.get('Class Quota', 'Not Found'),
        specific_data.get('Waitlist Maximum', 'Not Found'),
        specific_data.get('Instructor', 'Not Found')
    ] + table_data  # Append the table row data to the specific data
    
    # Append the extracted data to the list
    all_data.append(combined_row)

# Create a DataFrame from the list of dictionaries
df = pd.DataFrame(all_data, columns=column_names)

# Check if DataFrame is not empty before saving
if not df.empty:
    df.to_csv('fall2024.csv', index=False)
    print("Data written to output.csv successfully.")
else:
    print("DataFrame is empty. No data to write.")
