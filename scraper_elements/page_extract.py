import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

def extract_processed_features(url):
    """
    Extract and process features from a Funda advertisement URL.
    
    Args:
        url (str): The Funda advertisement URL to scrape
        
    Returns:
        dict: Processed features dictionary wrapped in a JSON structure, or None if extraction fails
    """
    # Make the request
    try:
        response = requests.get(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}, 
            timeout=10
        )
        response.raise_for_status()
        html = response.text
    except requests.RequestException as e:
        print(f"Request failed for {url}: {e}")
        return None

    # Extract raw features
    try:
        soup = BeautifulSoup(html, 'html.parser')
        features = {}
        
        # Check for renovation keywords
        features['kluswoning'] = 'yes' if any(keyword in soup.get_text().lower() 
                                            for keyword in ['klus', 'renov']) else 'no'
        
        # Base configuration for feature extraction
        dt_dd = {'next_tag': 'dd'}
        dt_dd_price = {**dt_dd, 'target_tag': 'span', 'target_class': None}
        
        # Feature mapping configuration
        mappings = {
            'price': {'find_by': 'dt', 'find_values': ['Vraagprijs', 'Laagste vraagprijs', 'Laatste vraagprijs'], **dt_dd_price},
            'living_area': {'find_by': 'dt', 'find_value': 'Wonen', **dt_dd},
            'volume': {'find_by': 'dt', 'find_value': 'Inhoud', **dt_dd},
            'rooms': {'find_by': 'dt', 'find_value': 'Aantal kamers', **dt_dd},
            'energy_label': {'find_by': 'dt', 'find_value': 'Energielabel', **dt_dd},
            'vve_contribution': {'find_by': 'dt', 'find_value': 'Bijdrage VvE', **dt_dd},
            'heating_system': {'find_by': 'dt', 'find_value': 'Verwarming', **dt_dd},
            'apartment_type': {'find_by': 'dt', 'find_value': 'Soort appartement', **dt_dd},
            'construction_type': {'find_by': 'dt', 'find_value': 'Soort bouw', **dt_dd},
            'build_year': {'find_by': 'dt', 'find_value': 'Bouwjaar', **dt_dd},
            'address': {'find_by': 'span', 'find_value': 'block text-2xl font-bold md:text-3xl lg:text-4xl', 'by_class': True},
            'postal_city': {'find_by': 'span', 'find_value': 'text-neutral-40', 'by_class': True, 
                          'parent_tag': 'h1', 'parent_class': 'object-header__container'}
        }
        
        # Extract features based on mapping
        for key, params in mappings.items():
            try:
                if params.get('parent_tag'):
                    parent = soup.find(params['parent_tag'], class_=params['parent_class'])
                    element = parent.find(params['find_by'], class_=params['find_value']) if parent else None
                elif params.get('by_class'):
                    element = soup.find(params['find_by'], class_=params['find_value'])
                elif key == 'price':
                    for label in params['find_values']:
                        if element := soup.find(params['find_by'], string=label):
                            features[key] = element.find_next('dd').text.strip()
                            break
                    continue
                else:
                    element = soup.find(params['find_by'], string=params['find_value'])
                    if element and params.get('next_tag'):
                        element = element.find_next(params['next_tag'])
                        if params.get('target_tag'):
                            element = element.find(params['target_tag'], class_=params['target_class'])
                
                if key != 'price':
                    features[key] = element.text.strip() if element else None
            except:
                features[key] = None
        
        features['extraction_timestamp'] = datetime.now().isoformat()

        # Process the features
        current_year = datetime.now().year
        processed = features.copy()
        
        # Process numerical values
        for field, replacements in {
            'price': ['€', '.', 'kosten koper'],
            'living_area': ['m²', '²'],
            'volume': ['m³', '³']
        }.items():
            if processed[field]:
                value = processed[field]
                for r in replacements:
                    value = value.replace(r, '')
                processed[field] = int(''.join(filter(str.isdigit, value.strip()))) if value else None
        
        # Calculate price per m2
        if processed['price'] and processed['living_area']:
            processed['price_per_m2'] = round(processed['price'] / processed['living_area'])
        
        # Process VvE contribution
        if processed['vve_contribution']:
            try:
                value = processed['vve_contribution'].replace('€', '').replace(',', '.')
                processed['vve_contribution'] = float(''.join(c for c in value if c.isdigit() or c == '.'))
            except:
                processed['vve_contribution'] = None
        
        # Process building year and age
        if processed['build_year']:
            if year := ''.join(filter(str.isdigit, processed['build_year'])):
                processed['building_age'] = current_year - int(year)
                processed['build_year'] = int(year)
        
        # Process rooms
        if processed['rooms']:
            processed['rooms'] = next((int(c) for c in processed['rooms'] if c.isdigit()), None)
        
        # Process energy label
        if processed['energy_label']:
            processed['energy_label'] = processed['energy_label'].split('Wat')[0].strip()
        
        # Process postal code and city
        if processed['postal_city'] and (parts := processed['postal_city'].split()):
            processed.update({
                'PC4': parts[0] if len(parts[0]) == 4 and parts[0].isdigit() else None,
                'PC6': parts[1] if len(parts) > 1 else None,
                'city': ' '.join(parts[2:]) if len(parts) > 2 else None
            })
        else:
            processed.update({'PC4': None, 'PC6': None, 'city': None})
        
        # Create ordered features dictionary
        ordered_features = {
            "features": {
                "kluswoning": processed.get('kluswoning'),
                "price": processed.get('price'),
                "living_area": processed.get('living_area'),
                "volume": processed.get('volume'),
                "rooms": processed.get('rooms'),
                "energy_label": processed.get('energy_label'),
                "vve_contribution": processed.get('vve_contribution'),
                "heating_system": processed.get('heating_system'),
                "apartment_type": processed.get('apartment_type'),
                "construction_type": processed.get('construction_type'),
                "build_year": processed.get('build_year'),
                "address": processed.get('address'),
                "postal_city": processed.get('postal_city'),
                "building_age": processed.get('building_age'),
                "PC4": processed.get('PC4'),
                "PC6": processed.get('PC6'),
                "city": processed.get('city'),
                "extraction_timestamp": processed.get('extraction_timestamp'),
                "price_per_m2": processed.get('price_per_m2')
            }
        }
        
        return ordered_features

    except Exception as e:
        print(f"Feature extraction failed for {url}: {e}")
        return None

# Example usage (only if run directly)
if __name__ == "__main__":
    url = "https://www.funda.nl/detail/koop/den-haag/appartement-martinus-nijhoffweg-107/43819404/"
    features = extract_processed_features(url)
    if features:
        print("Extracted and processed features:")
        print(json.dumps(features, indent=2))
    else:
        print("Could not extract features from the page")