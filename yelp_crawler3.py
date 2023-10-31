import requests
import json
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

# Constants
CATEGORY = 'Delivery'
LOCATION = 'South San Francisco, CA'
BASE_URL = 'https://www.yelp.com/search'
BUSINESS_URL = 'https://www.yelp.com'
OUTPUT_FILE = "output.json"


def get_list_of_business():
    # Set up initial search parameters
    params = {
        'find_desc': CATEGORY,
        'find_loc': LOCATION,
        'start': '0'
    }

    data = []

    while True:
        response = requests.get(BASE_URL, params=params)

        if response.status_code != 200:
            print(f"Request failed with status code {response.status_code}")
            break

        soup = BeautifulSoup(response.content, 'html.parser')
        h3_elements = soup.findAll('h3')

        for h3 in h3_elements:
            a = h3.find('a')
            if a:
                href = a.get('href')
                name = a.text
                data.append({'href': href, 'name': name})

        # Check for pagination link to the next page
        next_page_link = soup.find('a', class_='next-link')
        if next_page_link:
            next_page_url = urljoin(BASE_URL, next_page_link.get('href'))
            start_param = parse_qs(urlparse(next_page_url).query).get('start')
            if start_param:
                params['start'] = int(start_param[0])
                print(f"Scraping next page with start parameter: {int(start_param[0])}")
            else:
                break
        else:
            break

    print(f"Scraped {len(data)} businesses")
    get_business_info(data)


def get_business_info(data):
    result = []
    for business_data in data:
        business_url = BUSINESS_URL + business_data['href']
        print(business_url)
        response = requests.get(business_url)

        # Initialize data_for_json for the current business
        data_for_json = {
            'Business name': business_data['name'],
            'Business yelp url': business_url,
            'Business rating': 'N/A',
            'Number of reviews': 'N/A',
            'Business website': 'N/A',
            'Reviewers': []
        }

        if response.status_code != 200:
            print(f"Request failed with status code {response.status_code}")
        else:
            soup = BeautifulSoup(response.content, 'html.parser')
            time.sleep(0.5)

            # Get business rating
            try:
                business_rating = soup.find('div', {'aria-label': True})['aria-label']
                data_for_json['Business rating'] = business_rating
            except TypeError:
                pass

            # Get number of reviews
            num_reviews_element = soup.find('a', text=lambda text: text and "reviews" in text)
            if num_reviews_element:
                num_reviews = num_reviews_element.text
                data_for_json['Number of reviews'] = num_reviews

            # Get business website
            website_element = soup.find('a', {'rel': 'noopener', 'role': 'link'})
            if website_element:
                business_website = website_element.text
                data_for_json['Business website'] = business_website

            # Count the occurrences of "N/A"
            cnt_na = list(data_for_json.values()).count("N/A")

            if cnt_na > 2:
                time.sleep(5)

            div_elements = soup.find_all('div', class_=lambda x: x and x.startswith('user-passport-info'))
            for div in div_elements:
                if div.a:
                    name_of_reviewer = div.a.text
                    location_of_reviewer = div.find_all('span')[-1].text
                    data_for_json['Reviewers'].append({'Name': name_of_reviewer, 'Region': location_of_reviewer})

            result.append(data_for_json)

    # Write the JSON data to the file
    with open(OUTPUT_FILE, "a") as output_file:
        for business_data in result:
            json.dump(business_data, output_file)
            output_file.write("\n")

    print(f"Scraped details of {len(result)} businesses")


# Set your CATEGORY and LOCATION variables before calling the function
get_list_of_business()
