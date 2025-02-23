import requests
from bs4 import BeautifulSoup
from pathlib import Path

def get_eligible_links(url):
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        with open(Path(__file__).parent.parent / 'data' / 'zipcodes.txt') as f:
            valid_zipcodes = {code.strip() for code in f.read().strip('[]').replace("'", "").replace(" ", "").split(',') if code.strip()}
        
        return [
            f"https://www.funda.nl{link['href']}"
            for link in soup.find_all('a', href=lambda x: x and '/detail/koop/' in x)
            if (div := link.find('div', class_='truncate text-neutral-80'))
            and div.text.strip()[:4].isdigit()
            and div.text.strip()[:4] in valid_zipcodes
        ]
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return []
