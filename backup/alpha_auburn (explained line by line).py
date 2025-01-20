from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import re
import numpy as np
from datetime import datetime

from google.cloud import storage
import io


""" dependencies above explained...

from playwright.sync_api import sync_playwright
-> Imports sync_playwright from the playwright library, which is used for browser automation

from bs4 import BeautifulSoup
-> BeautifulSoup is a Python library for parsing HTML and XML documents. It's often used to scrape data from websites by navigating and extracting information from HTML structures.

import pandas as pd
-> pandas is a powerful data manipulation and analysis library, often used for handling tabular data. It's particularly useful for data analysis, working with DataFrames (which are like tables). Pandas DataFrame is a tabular data structure (you have rows and columns of data) in Python. You can modify, filter, sort, or aggregate the data within a DataFrame. DataFrame is compatible with many data formats (CSV, Excel, SQL, etc.) and can easily be exported or imported from these formats.

import re
-> re provides support for regular expressions (regex).

import numpy as np
-> numpy is a library used for numerical operations and working with arrays.

from datetime import datetime
-> This is used for working with dates and times, such as getting the current date/time, formatting dates, or performing date calculations.

from google.cloud import storage
-> Imports the storage module from the google.cloud library. This allows interaction with Google Cloud Storage, which is a cloud-based file storage service. You can use this to upload, download, and manage files in cloud storage

import io
-> io provides tools for working with streams of data (like reading from or writing to files). It is often used when you need to work with data in-memory without writing to disk.


"""



##### Functions ###############

def upload_dataframe_to_gcs(bucket_name, df, destination_blob_name):
    """Uploads a Pandas DataFrame to Google Cloud Storage as a CSV."""

    try:
        # Convert DataFrame to CSV string in memory
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')  # Important: Use UTF-8 encoding
        csv_content = csv_buffer.getvalue()

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_string(csv_content, content_type='text/csv')

        print(f"DataFrame uploaded to gs://{bucket_name}/{destination_blob_name}")
        return True # Return true if successfull
    except Exception as e:
        print(f"An error occurred: {e}")
        return False # Return false if there is an error

def extract_data_from_html(html_content):
    """Extracts court, class, and titles from an HTML file.

    Args:
        filepath: The path to the HTML file.

    Returns:
        A Pandas DataFrame or None if an error occurs.
    """


    # Find all tr tags with class starting with 'trSchemaLane'
    tr_tags = re.findall(r"(<tr class=\"trSchemaLane.*?</tr>)", html_content, re.DOTALL)
    # Returns:
    # [
    #   '<tr class="trSchemaLane_65">...',
    #   '<tr class="trSchemaLane_66">...'
    # ]

    # Initialize dictionaries and list for storing data
    combined_html = {}
    data = []
    # Process each tr tag found
    for tr_html in tr_tags:
        # Create a BeautifulSoup object for this specific tr tag
        soup_tr = BeautifulSoup(tr_html, "html.parser")
        # Find the tr tag that has a class starting with 'trSchemaLane'
        tr_tag = soup_tr.find('tr', class_=lambda x: x and x.startswith('trSchemaLane'))
        if tr_tag:
            # Find the span tag containing court number
            court_span = tr_tag.find('span') # finds <span>Court 1</span> in the first iteration
            court_number = court_span.text if court_span else None
            # Get the class name from the tr tag
            class_name = tr_tag.get('class')[0] if tr_tag and tr_tag.get('class') else None
            # Find all td tags with class 'tooltip' and get their title attributes. These contain the booking information
            title_texts = [td.get('title') for td in tr_tag.find_all('td', {'class': 'tooltip'}) if td.get('title')] #finds all titles within current tr
            """ would look like this..
            title_texts = [
                "9:00am - available",
                "10:00am - booked"
            ]
            """
            # then add to data list (dictionary)
            data.append({
            "Court": court_number,
            "Class": class_name,
            "Titles": title_texts
            })

            """ data list would look like this..
            data = [
                {
                    "Court": "Court 1",
                    "Class": "trSchemaLane_65",
                    "Titles": ["9:00am - available", "10:00am - booked"]
                },
                {
                    "Court": "Court 2",
                    "Class": "trSchemaLane_66",
                    "Titles": ["9:00am - booked", "10:00am - available"]
                }
            ]

            """


    #for html_string in combined_html.values():
    ##    soup = BeautifulSoup(html_string, 'html.parser')
    #    tr_tag = soup.find('tr', class_=lambda x: x and x.startswith('trSchemaLane'))
    #    if tr_tag:
    #        court_span = tr_tag.find('span')
    #        court_number = court_span.text if court_span else None
    #        title_texts = [td.get('title') for td in tr_tag.find_all('td', {'class': 'tooltip'}) if td.get('title')]
    #        data.append({"Court": court_number, "Class": class_name, "Titles": title_texts})

    # Convert the list of dictionaries to a pandas DataFrame
    df = pd.DataFrame(data)
    return df
    # Returns:
    #    Court            Class                                    Titles
    # 0  Court 1  trSchemaLane_65  [9:00am - available, 10:00am - booked]
    # 1  Court 2  trSchemaLane_66  [9:00am - booked, 10:00am - available]


def split_html_by_date(html_content):
    """Splits HTML content into parts based on date headings.

    Args:
        html_content: The HTML content as a string.

    Returns:
        A dictionary where keys are dates and values are the corresponding HTML parts.
        Returns None if no dates are found.
    """

    """ for example, imagine you have the following in html_content
    <h3>Monday, 13th Jan 2025</h3>
        <tr class="trSchemaLane_65">
            <span>Court 1</span>
            <td class="tooltip" title="9:00am - available"></td>
            <td class="tooltip" title="10:00am - booked"></td>
        </tr>
        <tr class="trSchemaLane_66">
            <span>Court 2</span>
            <td class="tooltip" title="9:00am - booked"></td>
            <td class="tooltip" title="10:00am - available"></td>
        </tr>

        <h3>Tuesday, 14th Jan 2025</h3>
        <tr class="trSchemaLane_65">
            <span>Court 1</span>
            <td class="tooltip" title="9:00am - booked"></td>
            <td class="tooltip" title="10:00am - available"></td>
        </tr>
        <tr class="trSchemaLane_66">
            <span>Court 2</span>
            <td class="tooltip" title="9:00am - available"></td>
            <td class="tooltip" title="10:00am - booked"></td>
        </tr>


    """


    soup = BeautifulSoup(html_content, 'html.parser')
    #First, it finds all h3 tags (date headings)
    date_headings = soup.find_all('h3')
    #Returns: ['Monday, 13th Jan 2025', 'Tuesday, 14th Jan 2025']

    if not date_headings:
        return None

    # Initialize empty dictionary to store results
    split_data = {}

    # Loop through each h3 heading with its index
    for i, heading in enumerate(date_headings):
    """
    When we use enumerate(date_headings), it creates an iterator that yields pairs of index numbers and values. So:
    pythonCopyfor i, heading in enumerate(date_headings):
        print(f"i = {i}, heading = {heading}")

    # Output would be:
    # i = 0, heading = <h3>Monday, 13th Jan 2025</h3>
    # i = 1, heading = <h3>Tuesday, 14th Jan 2025</h3>
    """
        # Get the text from the heading (the date) and remove whitespace
        date_text = heading.text.strip()
        # First iteration would return "Monday, 13th Jan 2025"
        # Set current heading as start point
        start_tag = heading
        # start_tag = <h3>Monday, 13th Jan 2025</h3>      <--- for the first iteration (i = 0)
        # Set next heading as end point, or None if this is the last heading
        end_tag = date_headings[i + 1] if i + 1 < len(date_headings) else None
        # end_tag = <h3>Tuesday, 14th Jan 2025</h3>       <--- for the first iteration (i = 0)
        # Initialize empty string for this section's HTML
        html_part = ""
        # Start with the heading
        current_tag = start_tag
        # Keep adding tags until we reach the next heading. This while loop collects all HTML between current heading and next heading
        while current_tag != end_tag:
            # Convert current tag to string and add to html_part
            html_part += str(current_tag)

            # Move to next tag in the HTML
            current_tag = current_tag.next_sibling

            # If no more tags, break the loop
            if current_tag is None:
                break  # Stop if we reach the end of the document

        # Process this section's HTML and store in dictionary with date as key
        split_data[date_text] = extract_data_from_html(html_part) #the DataFrame is returned and becomes the value in the split_data dictionary

    # Return the completed dictionary
    return split_data

def convert_date_string(date_string):
    """Converts a date string like "Monday, 23th&nbsp;Dec&nbsp;2024" to "YYYY-MM-DD".

    Args:
        date_string: The date string to convert.

    Returns:
        The date in "YYYY-MM-DD" format as a string, or None if parsing fails.
    """
    date_string = date_string.replace(u'\xa0', " ") #This is the fix.
    match = re.match(r"(\w+), (\d+)(?:st|nd|rd|th) (\w+) (\d+)", date_string)
    if match:
        day_name = match.group(1)
        day = int(match.group(2))
        month_name = match.group(3)
        year = int(match.group(4))

        try:
          date_object = datetime.strptime(f"{day} {month_name} {year}", "%d %b %Y")
          return date_object.strftime("%Y-%m-%d")
        except ValueError:
          return None
    else:
        return None

##### Scrape the bookings ####
# Initialize Playwright and launch browser
playwright = sync_playwright().start()
browser = playwright.chromium.launch()
page = browser.new_page()
# Navigate to the booking website
page.goto('https://alphabadminton.yepbooking.com.au/')

# Try to close initial popup if it exists
try:
    close_button = page.query_selector(".ui-icon-closethick")
    close_button.click()
except: #except means exception and contains the code that will run if an exception occurs in the try block.
    print("button already clicked")

page.get_by_text("Alpha Auburn (22 Courts)").click()

# Try to close another popup that might appear after location selection
try:
    close_button = page.query_selector(".ui-icon-closethick")
    close_button.click()
except:
    print("button already clicked")

# Wait for 2 seconds to let the page load
page.wait_for_timeout(2000)
# Set the view to weekly schedule
page.select_option("#prehled", value="week")
# Wait another 2 seconds for the weekly view to load
page.wait_for_timeout(2000)


# Initialize a string to store all the HTML content
auburn_bookings = ""
# Add the current week's content to the string
auburn_bookings += page.content()

#alternative below
#with open('slough_week_0.html', "w+", encoding="utf-8") as f:
#    f.write(page.content())

# Loop to get the next 4 weeks of booking data
for i in range(4):
    page.wait_for_timeout(2000)
    # Click the "next week" button (gets the last instance of nextDateMover)
    page.locator("#nextDateMover").nth(-1).click()
    page.wait_for_timeout(2000)
    # Calculate which week we're on (1-4)
    week = i + 1
    #html_name = 'slough_week_' + str(week) + '.html'
    #with open(html_name, "w+", encoding="utf-8") as f:
    #    f.write(page.content())
    # Add this week's content to our string of HTML content
    auburn_bookings += page.content()

# Clean up by closing the browser and stopping Playwright
browser.close()
playwright.stop()

######## Create dataframe ##############################

# Split the HTML content into separate DataFrames by date.
split_schemas = split_html_by_date(auburn_bookings)
""" This involves a long convoluted process whereby the output would look like

split_html_by_date returns split_data where

split_data = {
    'Monday, 13th Jan 2025': DataFrame({
        'Court': ['Court 1', 'Court 2'],
        'Class': ['trSchemaLane_65', 'trSchemaLane_66'],
        'Titles': [
            ['9:00am - available', '10:00am - booked'],
            ['9:00am - booked', '10:00am - available']
        ]
    }),
    'Tuesday, 14th Jan 2025': DataFrame({
        'Court': ['Court 1', 'Court 2'],
        'Class': ['trSchemaLane_65', 'trSchemaLane_66'],
        'Titles': [
            ['9:00am - booked', '10:00am - available'],
            ['9:00am - available', '10:00am - booked']
        ]
    })
}

where dates like 'Monday, 13th Jan 2025' will be the key
and
DataFrame(....) will be df
"""

# Initialize empty list to store DataFrames
dfs = []

# For each date and its corresponding DataFrame add date information to each DataFrame
for key, df in split_schemas.items():
    df['key'] = key
    dfs.append(df)

# Combine all dates into one DataFrame
combined_df = pd.concat(dfs, ignore_index=True)

""" After adding 'key' column and concatenating:
combined_df:
   Court            Class                                    Titles                    key
0  Court 1  trSchemaLane_65  [9:00am - available, 10:00am - booked]   Monday, 13th Jan 2025
1  Court 2  trSchemaLane_66  [9:00am - booked, 10:00am - available]   Monday, 13th Jan 2025
2  Court 1  trSchemaLane_65  [9:00am - booked, 10:00am - available]   Tuesday, 14th Jan 2025
3  Court 2  trSchemaLane_66  [9:00am - available, 10:00am - booked]   Tuesday, 14th Jan 2025

"""

# Group by Class and date to get maximum Titles value
# This consolidates multiple bookings for the same court/class/date
df_union_max = combined_df.groupby(['Class','key'])['Titles'].max().reset_index()

# Merge court information with booking details
df_union_final = combined_df[['Court','Class','key']].drop_duplicates().merge(df_union_max, on=['Class','key'], how='left')

# Extract the location based on class number
df_union_final['Class_Number'] = df_union_final['Class'].str.extract(r'_(\d+)').astype(int)
df_union_final['Location'] = np.where(df_union_final['Class_Number'] < 37, 'Alpha Slough',  np.where(df_union_final['Class_Number'] < 65, 'Alpha Egerton', 'Alpha Auburn'))

""" After extracting Class_Number and determining Location:
df_union_final:
   Court            Class    Class_Number    Location                                    Titles                    key
0  Court 1  trSchemaLane_65        65      Alpha Auburn  [9:00am - available, 10:00am - booked]   Monday, 13th Jan 2025
1  Court 2  trSchemaLane_66        66      Alpha Auburn  [9:00am - booked, 10:00am - available]   Monday, 13th Jan 2025
2  Court 1  trSchemaLane_65        65      Alpha Auburn  [9:00am - booked, 10:00am - available]   Tuesday, 14th Jan 2025
3  Court 2  trSchemaLane_66        66      Alpha Auburn  [9:00am - available, 10:00am - booked]   Tuesday, 14th Jan 2025
"""

# Keep only relevant columns
df_union_final = df_union_final[['Location','Court','Titles','key']]

# Expand the Titles column (which contains lists of bookings) into separate rows
df_union_final = df_union_final.explode('Titles')

""" After keeping only relevant columns and exploding Titles:
df_union_final:
   Location     Court                     Titles                    key
0  Alpha Auburn  Court 1            9:00am - available    Monday, 13th Jan 2025
1  Alpha Auburn  Court 1            10:00am - booked     Monday, 13th Jan 2025
2  Alpha Auburn  Court 2            9:00am - booked      Monday, 13th Jan 2025
3  Alpha Auburn  Court 2            10:00am - available  Monday, 13th Jan 2025
4  Alpha Auburn  Court 1            9:00am - booked      Tuesday, 14th Jan 2025
5  Alpha Auburn  Court 1            10:00am - available  Tuesday, 14th Jan 2025
6  Alpha Auburn  Court 2            9:00am - available   Tuesday, 14th Jan 2025
7  Alpha Auburn  Court 2            10:00am - booked     Tuesday, 14th Jan 2025
"""

# Split booking information into Time and Status
df_union_final[['Time', 'Status']] = df_union_final['Titles'].str.split(' - ', n=1, expand=True)

""" After splitting Titles into Time and Status:
df_union_final:
   Location     Court        Time      Status                    key
0  Alpha Auburn  Court 1    9:00am     available    Monday, 13th Jan 2025
1  Alpha Auburn  Court 1    10:00am    booked      Monday, 13th Jan 2025
2  Alpha Auburn  Court 2    9:00am     booked      Monday, 13th Jan 2025
3  Alpha Auburn  Court 2    10:00am    available   Monday, 13th Jan 2025
4  Alpha Auburn  Court 1    9:00am     booked      Tuesday, 14th Jan 2025
5  Alpha Auburn  Court 1    10:00am    available   Tuesday, 14th Jan 2025
6  Alpha Auburn  Court 2    9:00am     available   Tuesday, 14th Jan 2025
7  Alpha Auburn  Court 2    10:00am    booked      Tuesday, 14th Jan 2025

"""

# Clean up and format data
df_union_final.drop(columns='Titles',axis=1,inplace=True)
df_union_final['Time'] = df_union_final['Time'].str.extract(r'(\d+:\d+[ap]m)')

# Filter for Alpha Auburn location and remove invalid entries
df_union_final = df_union_final[df_union_final['Location'] == 'Alpha Auburn']
df_union_final = df_union_final[df_union_final['Court'] != ""]
df_union_final = df_union_final[df_union_final['Court'].notna()]
df_union_final = df_union_final[df_union_final['Status'].notna()]

# Convert dates to standard format and create DateTime column
df_union_final['Date'] = df_union_final['key'].apply(convert_date_string)
df_union_final.drop(columns='key',axis=1,inplace=True)
df_union_final['DateTime'] = df_union_final['Date'] + " " + df_union_final['Time']

"""
df_union_final:
   Location     Court        Time      Status          Date        DateTime
0  Alpha Auburn  Court 1    9:00am     available    2025-01-13    2025-01-13 9:00am
1  Alpha Auburn  Court 1    10:00am    booked      2025-01-13    2025-01-13 10:00am
2  Alpha Auburn  Court 2    9:00am     booked      2025-01-13    2025-01-13 9:00am
3  Alpha Auburn  Court 2    10:00am    available   2025-01-13    2025-01-13 10:00am
4  Alpha Auburn  Court 1    9:00am     booked      2025-01-14    2025-01-14 9:00am
5  Alpha Auburn  Court 1    10:00am    available   2025-01-14    2025-01-14 10:00am
6  Alpha Auburn  Court 2    9:00am     available   2025-01-14    2025-01-14 9:00am
7  Alpha Auburn  Court 2    10:00am    booked      2025-01-14    2025-01-14 10:00am
"""

# Get the minimum and maximum dates from the DataFrame
min_date = df_union_final['Date'].min() # Would be '2025-01-13'
max_date = df_union_final['Date'].max() # Would be '2025-01-14'

# Create a range of dates from min_date to max_date with daily frequency
daily_range = pd.date_range(start=min_date, end=max_date, freq='D')

# Define all possible time slots for bookings
times = [
    "9:00am", "10:00am", "11:00am", "12:00pm",
    "1:00pm", "2:00pm", "3:00pm", "4:00pm", "5:00pm", "6:00pm",
    "7:00pm", "8:00pm", "9:00pm", "10:00pm"
]

# Define all court numbers at the venue
courts = [
    "Court 1", "Court 2", "Court 3", "Court 4", "Court 5", "Court 6",
    "Court 7", "Court 8", "Court 9", "Court 10", "Court 11", "Court 12",
    "Court 13", "Court 14", "Court 15", "Court 16", "Court 17", "Court 18",
    "Court 19", "Court 20", "Court 21", "Court 22"
]

# Initialize empty lists to store the cartesian product of dates, times, and courts
date_time_list = []
date_list = []
time_list = []
courts_list = []

# Create a cartesian product of all dates, times, and courts
for date in daily_range:
    for time_str in times:
        for court in courts:
            # Combine date and time
            date_time_str = str(date.date()) + " " + time_str
            # Example: "2025-01-13 9:00am"
            date_time_list.append(date_time_str)
            date_list.append(date.date())
            time_list.append(time_str)
            courts_list.append(court)

# Create a DataFrame with all possible combinations
date_time_df = pd.DataFrame({'Date': date_list, 'Time': time_list, 'DateTime': date_time_list, 'Court':courts_list})
date_time_df['Location'] = 'Alpha Auburn'


# Merge the actual booking data with all possible combinations
df_union_final = date_time_df.merge(df_union_final, on=['DateTime','Court','Location'], how='left')

# Fill in missing status values as 'available'
df_union_final['Status'] = np.where(df_union_final['Status'].isnull(), 'available', df_union_final['Status'])

# Convert all non-available statuses to 'unavailable'
df_union_final['Status'] = np.where(df_union_final['Status'] != 'available' , 'unavailable', df_union_final['Status'])

# Clean up column names and select final columns
df_union_final = df_union_final.rename(columns={'Date_x': 'Date', 'Time_x': 'Time'})
df_union_final = df_union_final[['Location','Court','Date','Time','Status']]

#df_union_final.to_csv('alpha_auburn_bookings.csv', index=False)
#print(df_union_final)


bucket_name = "badminton-bookings"
blob_name = "alpha_auburn_bookings.csv"

if upload_dataframe_to_gcs(bucket_name, df_union_final, blob_name):
    print("Upload successful")
else:
    print("Upload failed")