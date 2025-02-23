import sys
import os
import time
import json
from scraper_elements.nav_extract import get_eligible_links
from scraper_elements.page_extract import extract_processed_features

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Define base URL with search parameters
first_page = ("https://www.funda.nl/zoeken/koop?"
             "selected_area=[%22provincie-zuid-holland%22,%22provincie-noord-holland%22,%22utrecht%22]&"
             "price=%22175000-225000%22&"
             "availability=[%22available%22,%22negotiations%22,%22unavailable%22]")


def gather_links(num_pages=1):
    all_links = []
    for page_num in range(1, num_pages + 1):
        current_page = f"{first_page}&page={page_num}"
        all_links.extend(get_eligible_links(current_page))
        print(f"Gathered links from page {page_num}")
        time.sleep(2)
    return all_links

def process_houses(links):
    houses_data = []
    for i, link in enumerate(links, 1):
        try:
            houses_data.append(extract_processed_features(link))
            print(f"Processed house {i}/{len(links)}: {link}")
        except Exception as e:
            print(f"Error processing house {i}: {link}\nError: {str(e)}")
        time.sleep(2)
    return houses_data

def main():
    print("Starting to gather house links...")
    links = gather_links()
    print(f"Total links gathered: {len(links)}")
    
    print(f"Starting to extract features from {len(links)} houses...")
    houses_data = process_houses(links)
    
    # Save features
    with open('houses_features.json', 'w', encoding='utf-8') as f:
        json.dump(houses_data, f, indent=2, ensure_ascii=False)
    print("Feature extraction completed!")

if __name__ == "__main__":
    main()
