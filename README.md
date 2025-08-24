# Wasserpegel Crawler

This project contains a Python web crawler to extract water level data and station master data from the Bavarian flood information service website.

## Description

The crawler fetches data from the website of the Hochwassernachrichtendienst Bayern (https://www.hnd.bayern.de). It is designed to be adaptable for different measurement stations.

The current implementation successfully crawls both measured water levels (including forecast data) and detailed station master data, including geolocation coordinates. The crawler is functional and retrieves the correct data.

## Technologies

* Python
* requests (for fetching HTML)
* BeautifulSoup (for HTML parsing)
* pandas (for data structuring)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   ```
2. **Create and activate a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
   Or using conda:
   ```bash
   conda create -n wasserpegel_crawl python=3.9
   conda activate wasserpegel_crawl
   ```
3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To run the crawler, execute the `crawler.py` script with the desired mode:

```bash
# To crawl water level measurements and forecasts (default mode)
python crawler.py --mode measurements

# To crawl station master data (including geolocation)
python crawler.py --mode master_data
```

If you are using the conda environment, you can run the script with:

```bash
# To crawl water level measurements and forecasts (default mode)
conda run -n wasserpegel_crawl python crawler.py --mode measurements

# To crawl station master data (including geolocation)
conda run -n wasserpegel_crawl python crawler.py --mode master_data
```

The script will save the crawled data into the `data/` directory.

## Output Data Format

The crawler outputs pandas DataFrames saved as CSV files in the `data/` directory.

### Water Level Data (`data/water_levels.csv`)

| ColumnName       | Description                                         |
| ---------------- | --------------------------------------------------- |
| `DateTime`       | The timestamp of the reading (as a string).         |
| `Type`           | `measured` for actual readings, `forecast` for predictions. |
| `WaterLevel`     | The measured water level in cm. Empty for forecasts.|
| `Forecast_Lower` | The lower bound of the forecast range. Empty for measured values. |
| `Forecast_Upper` | The upper bound of the forecast range. Empty for measured values. |
| `Meldestufe`     | The current flood warning level for the station.    |

### Station Master Data (`data/station_master_data.csv`)

| ColumnName             | Description                                         |
| ---------------------- | --------------------------------------------------- |
| `Station`              | Name of the measurement station.                    |
| `Betreiber`            | Operator of the station.                            |
| `Messstellen-Nr.`      | Unique identification number of the station.        |
| `Einzugsgebiet`        | Catchment area in km².                              |
| `Flußkilometer`        | River kilometer.                                    |
| `Pegelnullpunktshöhe`  | Height of the gauge zero point.                     |
| `Gemeinde`             | Municipality where the station is located.          |
| `Landkreis`            | District where the station is located.              |
| `Ostwert`              | East coordinate (ETRS89 / UTM Zone 32N).            |
| `Nordwert`             | North coordinate (ETRS89 / UTM Zone 32N).           |
| `Datenfernübertragung` | Indicates if data is transmitted remotely.          |
| `Meldestufen`          | Flood warning levels (header).                      |
| `Meldebeginn`          | Start of flood warning level.                       |
| `Meldestufe 1`         | Water level for warning stage 1.                    |
| `Meldestufe 2`         | Water level for warning stage 2.                    |
| `Meldestufe 3`         | Water level for warning stage 3.                    |
| `Meldestufe 4`         | Water level for warning stage 4.                    |
| `Map_X`                | X-coordinate from map JavaScript (projected).       |
| `Map_Y`                | Y-coordinate from map JavaScript (projected).       |

## Recent Changes and Improvements

*   **Refactored Codebase:** Extracted common functionalities into helper functions (`_fetch_and_parse_url`, `_find_link_by_text`) to reduce redundancy and improve maintainability.
*   **Comprehensive Test Suite:** Implemented `pytest` tests (`test_crawler.py`) to ensure the correctness of data extraction for both measurements and master data.
*   **Organized Output:** All generated CSV files are now stored in a dedicated `data/` directory.
*   **Version Control:** The `data/` directory has been added to `.gitignore` to prevent generated data from being tracked by Git.