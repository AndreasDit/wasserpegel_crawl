import pytest
import pandas as pd
from crawler import get_station_data, crawl_station_data, crawl_station_master_data

# Define the test station
TEST_STATION_NAME = "Neu-Ulm"

@pytest.fixture(scope="module")
def neu_ulm_station():
    """Fixture to get the Neu-Ulm station data."""
    stations = get_station_data()
    for station in stations:
        if station['name'] == TEST_STATION_NAME:
            return station
    pytest.fail(f"Test station '{TEST_STATION_NAME}' not found in station list.")

def test_crawl_neu_ulm_measurements(neu_ulm_station):
    """Test crawling measurements for Neu-Ulm station."""
    station_df = crawl_station_data(neu_ulm_station['link'], neu_ulm_station['name'])
    
    assert station_df is not None
    assert not station_df.empty
    assert 'Station' in station_df.columns
    assert 'DateTime' in station_df.columns
    assert 'Type' in station_df.columns
    assert 'WaterLevel' in station_df.columns
    assert 'Forecast_Lower' in station_df.columns
    assert 'Forecast_Upper' in station_df.columns
    assert (station_df['Station'] == TEST_STATION_NAME).all()
    assert 'measured' in station_df['Type'].unique()

def test_crawl_neu_ulm_master_data(neu_ulm_station):
    """Test crawling master data for Neu-Ulm station."""
    station_df = crawl_station_master_data(neu_ulm_station['link'], neu_ulm_station['name'])
    
    assert station_df is not None
    assert not station_df.empty
    assert 'Station' in station_df.columns
    assert (station_df['Station'] == TEST_STATION_NAME).all()
    
    # Assert some expected master data fields
    assert 'Messstellen-Nr.' in station_df.columns
    assert 'Einzugsgebiet' in station_df.columns
    assert 'Flußkilometer' in station_df.columns
    assert 'Pegelnullpunktshöhe' in station_df.columns
    assert 'Gemeinde' in station_df.columns
    assert 'Landkreis' in station_df.columns
    assert 'Ostwert' in station_df.columns
    assert 'Nordwert' in station_df.columns
    assert 'Datenfernübertragung' in station_df.columns
    assert 'Meldestufen' in station_df.columns
    assert 'Meldebeginn' in station_df.columns
