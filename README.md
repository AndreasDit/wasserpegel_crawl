# Wasserpegel Crawler

This project contains a Python web crawler to extract water level data from the Bavarian flood information service website.

## Description

The crawler fetches data from the website of the Hochwassernachrichtendienst Bayern (https://www.hnd.bayern.de). It is designed to be adaptable for different measurement stations.

The current implementation crawls the data for the station "Schweinfurt Neuer Hafen" and extracts both measured water levels and forecast data.

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

To run the crawler, execute the `crawler.py` script:

```bash
python crawler.py
```

If you are using the conda environment, you can run the script with:

```bash
conda run -n wasserpegel_crawl python crawler.py
```

The script will print a pandas DataFrame to the console with the crawled data.

## Output Data Format

The crawler outputs a pandas DataFrame with the following columns:

| ColumnName       | Description                                         |
| ---------------- | --------------------------------------------------- |
| `DateTime`       | The timestamp of the reading (as a string).         |
| `Type`           | `measured` for actual readings, `forecast` for predictions. |
| `WaterLevel`     | The measured water level in cm. Empty for forecasts.|
| `Forecast_Lower` | The lower bound of the forecast range. Empty for measured values. |
| `Forecast_Upper` | The upper bound of the forecast range. Empty for measured values. |
