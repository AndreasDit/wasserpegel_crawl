
import requests
from bs4 import BeautifulSoup
import pandas as pd

def crawl_water_level_data():
    """
    Crawls water level data from the specified URL and returns it as a pandas DataFrame.
    """
    url = "https://www.hnd.bayern.de/pegel/unterer_main/schweinfurt-neuer-hafen-24022003/tabelle?methode=wasserstand&"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    
    table = None
    for t in soup.find_all('table'):
        if 'Datum' in t.text and 'Wasserstand' in t.text:
            table = t
            break

    if table is None:
        print("Could not find the data table on the page.")
        return None

    data = []
    for row in table.find_all('tr'):
        cols = row.find_all('td')
        if len(cols) == 2:
            date_time_str = cols[0].text.strip()
            water_level_str = cols[1].text.strip()

            # Check if it's a forecast or a measured value
            if '-' in water_level_str:
                value_type = 'forecast'
                lower, upper = water_level_str.split('-')
                data.append([date_time_str, value_type, '', lower.strip(), upper.strip()])
            else:
                value_type = 'measured'
                data.append([date_time_str, value_type, water_level_str, '', ''])

    if not data:
        print("No data found in the table.")
        return None

    df = pd.DataFrame(data, columns=['DateTime', 'Type', 'WaterLevel', 'Forecast_Lower', 'Forecast_Upper'])
    return df

if __name__ == '__main__':
    water_level_df = crawl_water_level_data()
    if water_level_df is not None:
        print(water_level_df)
