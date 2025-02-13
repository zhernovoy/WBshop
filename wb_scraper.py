import requests
from urllib.parse import urljoin, urlparse, parse_qs
import json

def extract_brand_id(url):
    """Extract brand ID from Wildberries URL"""
    path = urlparse(url).path
    
    # Handle different URL patterns
    if 'brands/' in url:
        # Format: /brands/310727407-teatr-teney-shadow-play
        parts = path.split('brands/')
        if len(parts) > 1:
            brand_part = parts[1].split('-')[0]  # Get first part before dash
            if brand_part.isdigit():
                return brand_part
    
    # Handle seller ID format
    if 'seller/' in url:
        # Format: /seller/310727407
        parts = path.split('seller/')
        if len(parts) > 1:
            seller_id = parts[1].split('/')[0]
            if seller_id.isdigit():
                return seller_id
    
    # Try to find any number in the URL that could be an ID
    parts = path.split('/')
    for part in parts:
        # Split by dash in case ID is part of a longer string
        subparts = part.split('-')
        for subpart in subparts:
            if subpart.isdigit() and len(subpart) > 5:  # Most WB IDs are long numbers
                return subpart
    
    raise ValueError("Could not find brand/seller ID in URL. Please ensure this is a valid Wildberries brand or seller URL.")

def get_prices_for_products(product_ids):
    """Get current prices for multiple products using Wildberries price API"""
    if not product_ids:
        return {}
    
    # New price API endpoint
    price_api_url = "https://card.wb.ru/cards/detail"
    
    try:
        prices = {}
        # Process products in chunks of 100 to avoid too long URLs
        chunk_size = 100
        for i in range(0, len(product_ids), chunk_size):
            chunk = product_ids[i:i + chunk_size]
            
            params = {
                'nm': ';'.join(map(str, chunk)),  # Using semicolon as separator
                'locale': 'ru',
                'reg': 1,
                'pricemarginCoeff': 1.0,
                'curr': 'rub',
                'dest': -1257786
            }
            
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'ru-RU,ru;q=0.9',
                'Origin': 'https://www.wildberries.ru',
                'Referer': 'https://www.wildberries.ru/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(
                price_api_url,
                params=params,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Debug print
            print(f"Price API Response for chunk {i}: {data}")
            
            for product in data.get('data', {}).get('products', []):
                product_id = str(product.get('id'))
                prices[product_id] = {
                    'original_price': product.get('priceU', 0) / 100,
                    'sale_price': product.get('salePriceU', 0) / 100,
                    'discount': product.get('discount', 0),
                    'promo_text': product.get('promoTextCard', '')
                }
        
        # Debug print
        if prices:
            print(f"Successfully fetched prices for {len(prices)} products")
        else:
            print("No prices were fetched")
            
        return prices
        
    except Exception as e:
        print(f"Warning: Failed to fetch prices: {e}")
        if 'response' in locals():
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text[:500]}")  # Print first 500 chars of response
        return {}

def get_items_from_wildberries(url):
    if not url.startswith('https://www.wildberries.ru/'):
        raise ValueError("Invalid URL. Must be a Wildberries URL")

    try:
        brand_id = extract_brand_id(url)
        print(f"Extracted brand ID: {brand_id}")  # Debug print
        
        # Updated endpoints with additional parameters
        endpoints = [
            f"https://catalog.wb.ru/sellers/catalog?seller={brand_id}&locale=ru&lang=ru&curr=rub&dest=-1257786&sort=popular&page=1&limit=100",
            f"https://catalog.wb.ru/brands/t/catalog?brand={brand_id}&locale=ru&lang=ru&curr=rub&dest=-1257786&sort=popular&page=1&limit=100"
        ]
        
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'ru-RU,ru;q=0.9',
            'Origin': 'https://www.wildberries.ru',
            'Referer': 'https://www.wildberries.ru/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        products = []
        success = False
        
        for api_url in endpoints:
            try:
                print(f"Trying endpoint: {api_url}")  # Debug print
                response = requests.get(
                    api_url,
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                
                data = response.json()
                print(f"Catalog API Response: {data}")  # Debug print
                
                product_ids = []
                temp_products = []
                
                for product in data.get('data', {}).get('products', []):
                    product_id = str(product.get('id', ''))
                    product_ids.append(product_id)
                    temp_products.append({
                        'id': product_id,
                        'name': product.get('name', ''),
                        'link': f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx"
                    })
                
                if temp_products:
                    prices = get_prices_for_products(product_ids)
                    for product in temp_products:
                        price_info = prices.get(product['id'], {})
                        product.update({
                            'original_price': price_info.get('original_price', 0),
                            'sale_price': price_info.get('sale_price', 0),
                            'discount': price_info.get('discount', 0),
                            'promo_text': price_info.get('promo_text', '')
                        })
                        products.append(product)
                    
                    success = True
                    break
                    
            except requests.RequestException as e:
                print(f"Request failed for endpoint: {e}")  # Debug print
                continue
        
        if not success:
            raise Exception("Could not fetch data from any endpoint")
            
        return products

    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}") 