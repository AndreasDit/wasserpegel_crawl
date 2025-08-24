import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib.parse
import argparse

def get_station_data():
    base_url = "https://www.hnd.bayern.de"
    list_page_url = f"{base_url}/pegel/meldestufen//tabellen"
    try:
        response = requests.get(list_page_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table')

        if not table:
            print("Could not find the station list table on the page.")
            return []

        stations = []
        for row in table.find_all('tr'):
            first_cell = row.find('td')
            if first_cell:
                link_tag = first_cell.find('a', href=True)
                if link_tag:
                    station_name = link_tag.get_text(strip=True)
                    primary_link_href = link_tag['href']
                    station_main_page_url = urllib.parse.urljoin(base_url, primary_link_href)
                    
                    stations.append({'name': station_name, 'link': station_main_page_url})

        return stations

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the station list: {e}")
        return []

def crawl_station_data(station_main_page_url, station_name):
    """
    Crawls water level data from a specific station's main page by finding the 'Tabelle' link
    and then extracting data from that table page.
    """
    try:
        # Fetch the station's main page
        response = requests.get(station_main_page_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the station main page {station_main_page_url}: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    # NEW: Check if 'Wasserstand' is present on the main page
    if "Wasserstand" not in soup.text:
        print(f"Skipping station {station_name} as 'Wasserstand' measurements are not found on its main page {station_main_page_url}.")
        return None
    
    # Find the 'Tabelle' link within the 'Ansicht' menu
    tabelle_link = None
    for link_tag in soup.find_all('a', string='Tabelle', href=True):
        tabelle_link = urllib.parse.urljoin(station_main_page_url, link_tag['href'])
        break # Take the first one found

    if not tabelle_link:
        print(f"Could not find 'Tabelle' link on the main page for station {station_name} at {station_main_page_url}.")
        return None

    # Now, fetch the 'Tabelle' page
    try:
        response = requests.get(tabelle_link)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the 'Tabelle' page {tabelle_link}: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # The rest of the function is the existing logic to parse the data table
    table = None
    for t in soup.find_all('table'):
        if 'Datum' in t.text and 'Wasserstand' in t.text:
            table = t
            break

    if table is None:
        print(f"Could not find the data table on the page for station {station_name} at {tabelle_link}.")
        return None

    data = []
    for row in table.find_all('tr'):
        cols = row.find_all('td')
        if len(cols) == 2:
            date_time_str = cols[0].text.strip()
            water_level_str = cols[1].text.strip()

            if '-' in water_level_str:
                value_type = 'forecast'
                parts = water_level_str.split('-', 1) 
                if len(parts) == 2:
                    lower, upper = parts
                    data.append([station_name, date_time_str, value_type, '', lower.strip(), upper.strip()])
                else:
                    print(f"Warning: Unexpected forecast format for {station_name}: {water_level_str}")
                    data.append([station_name, date_time_str, value_type, '', '', ''])
            else:
                value_type = 'measured'
                data.append([station_name, date_time_str, value_type, water_level_str, '', ''])

    if not data:
        print(f"No data found in the table for station {station_name} at {tabelle_link}.")
        return None

    df = pd.DataFrame(data, columns=['Station', 'DateTime', 'Type', 'WaterLevel', 'Forecast_Lower', 'Forecast_Upper'])
    return df

def crawl_station_master_data(station_main_page_url, station_name):
    """
    Crawls master data from a specific station's main page by finding the 'Stammdaten / Lagekarte / Bild' link
    and then extracting data from that page.
    """
    try:
        response = requests.get(station_main_page_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the station main page {station_main_page_url}: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the 'Stammdaten / Lagekarte / Bild' link
    master_data_link = None
    for link_tag in soup.find_all('a', href=True):
        if "Stammdaten / Lagekarte / Bild" in link_tag.get_text(strip=True):
            master_data_link = urllib.parse.urljoin(station_main_page_url, link_tag['href'])
            break

    if not master_data_link:
        print(f"Could not find 'Stammdaten / Lagekarte / Bild' link on the main page for station {station_name} at {station_main_page_url}.")
        return None

    # Now, fetch the master data page
    try:
        response = requests.get(master_data_link)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the master data page {master_data_link}: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    # Placeholder for extracting master data
    master_data = {'Station': station_name}

    # Find the table containing master data
    table = soup.find('table', class_='nobg')
    if table:
        for row in table.find_all('tr'):
            cols = row.find_all(['td', 'th']) # Use both td and th to capture headers if present
            if len(cols) == 2:
                key = cols[0].get_text(strip=True).replace(':', '') # Remove colon from key
                value = cols[1].get_text(strip=True)
                master_data[key] = value
            elif len(cols) == 1: # Handle rows with only one column, like "Meldestufen" header
                key = cols[0].get_text(strip=True)
                if key: # Only add if key is not empty
                    master_data[key] = "" # Add as a section header with empty value

    df = pd.DataFrame([master_data]) # Create DataFrame from a list of dictionaries
    return df

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crawl water level data or station master data.')
    parser.add_argument('--mode', type=str, default='measurements', 
                        choices=['measurements', 'master_data'],
                        help='Set the crawling mode: "measurements" (default) or "master_data".')
    args = parser.parse_args()
    CRAWL_MODE = args.mode

    stations = get_station_data()
    print(f"Found {len(stations)} stations.")
    if stations:
        all_data = []
        # No limit for demonstration purposes, crawl all stations
        for station in stations: 
            print(f"--------------------------------")
            print(f"Attempting to crawl data for station: {station['name']} from main page {station['link']}")
            
            if CRAWL_MODE == "measurements":
                station_df = crawl_station_data(station['link'], station['name'])
            elif CRAWL_MODE == "master_data":
                station_df = crawl_station_master_data(station['link'], station['name'])
            else:
                print(f"Invalid CRAWL_MODE: {CRAWL_MODE}")
                station_df = None

            if station_df is not None:
                print(f"Successfully crawled data for {station['name']}.")
                all_data.append(station_df)
            else:
                print(f"Failed to crawl data for {station['name']}.")

        if all_data:
            print(f"Collected data from {len(all_data)} stations. Concatenating...")
            combined_df = pd.concat(all_data, ignore_index=True)
            
            output_filename = 'water_levels.csv'
            if CRAWL_MODE == "master_data":
                output_filename = 'station_master_data.csv'

            combined_df.to_csv(output_filename, index=False)
            print(f"Successfully crawled and saved data to {output_filename}")
            print(combined_df.head())
        else:
            print("Could not crawl any data.")