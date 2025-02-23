import sys
import os
import json

# Add parent directory to Python path - this needs to come before the scraper_elements import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import from scraper_elements
from scraper_elements.nav_extract import get_eligible_links
from scraper_elements.page_extract import extract_processed_features

# Define base URL with search parameters for last 24 hours
BASE_URL = ("https://www.funda.nl/zoeken/koop?"
           "selected_area=[%22provincie-zuid-holland%22,%22provincie-noord-holland%22,%22utrecht%22]&"
           "price=%22175000-225000%22&"
           "publication_date=%221%22&"
           "availability=[%22available%22,%22negotiations%22,%22unavailable%22]")

# Get absolute path for the JSON file
JSON_PATH = os.path.join(os.path.dirname(__file__), 'recent_listings.json')

def load_existing_listings():
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("No existing database found. Creating new one.")
        return []

def update_listings():
    try:
        # Load existing listings and get their feature data
        existing_listings = load_existing_listings()
        existing_features = {str(house['features']) for house in existing_listings}
        
        # Get new links
        links = get_eligible_links(BASE_URL)
        print(f"Found {len(links)} links")
        
        # Process only new listings
        new_houses = []
        for i, link in enumerate(links, 1):
            try:
                print(f"Processing new house {i}/{len(links)}")
                house_data = extract_processed_features(link)
                # Only store if features are unique
                if str(house_data['features']) not in existing_features:
                    new_houses.append({'features': house_data['features']})
            except Exception as e:
                print(f"Error processing {link}: {str(e)}")
        
        # Combine existing and new listings
        updated_listings = existing_listings + new_houses
        
        # Save updated database
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(updated_listings, f, indent=2, ensure_ascii=False)
        print(f"Added {len(new_houses)} new houses to database")
        return updated_listings
        
    except Exception as e:
        print(f"Error gathering links: {str(e)}")
        return []

if __name__ == "__main__":
    update_listings()
