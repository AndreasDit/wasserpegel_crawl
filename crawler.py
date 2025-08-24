import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib.parse

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

if __name__ == '__main__':
    stations = get_station_data()
    print(f"Found {len(stations)} stations.")
    if stations:
        all_data = []
        # No limit for demonstration purposes, crawl all stations
        for station in stations: 
            print(f"--------------------------------")
            print(f"Attempting to crawl data for station: {station['name']} from main page {station['link']}")
            station_df = crawl_station_data(station['link'], station['name'])
            if station_df is not None:
                print(f"Successfully crawled data for {station['name']}.")
                all_data.append(station_df)
            else:
                print(f"Failed to crawl data for {station['name']}.")

        if all_data:
            print(f"Collected data from {len(all_data)} stations. Concatenating...")
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df.to_csv('water_levels.csv', index=False)
            print("Successfully crawled and saved data to water_levels.csv")
            print(combined_df.head())
        else:
            print("Could not crawl any data.")