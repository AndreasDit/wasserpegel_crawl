# Action Plan: Integrating the HND Bayern Crawler

This document outlines a detailed plan to integrate the new HND Bayern web crawler into the existing Pegelonline ETL pipeline. The primary goal is to enrich the dataset with additional data from the new source while adhering to the project's established coding style and architecture.

## 1. Guiding Principles

- **Preserve Existing Schema**: The final Parquet files (`stations.parquet`, `timeseries.parquet`, `current_water_level.parquet`,  `forecasts.parquet`) must retain their current data schema to ensure downstream compatibility.
- **Enrich Data**: The final output should contain the combined and merged data from both the Pegelonline API and the new HND crawler.
- **Maintain Coding Style**: All new code will use Dagster assets and the Polars library for data manipulation, mirroring the existing codebase.
- **Isolate Sources**: The initial data extraction from the two sources (Pegelonline API and HND website) will be kept in separate, independent assets to maintain modularity and clarity.

## 2. Phase 1: Refactor and Integrate Crawler Logic

The first step is to adapt the standalone `crawler.py` script into a reusable component within the Dagster framework.

- **Action 1.1: Create New Asset Module**
  - Create a new file: `src/etl/assets/hnd_bavaria.py`.
  - This file will house all assets related to the HND crawler.

- **Action 1.2: Relocate and Refactor Crawler Functions**
  - Move the core data scraping functions from `crawler.py` (`get_station_data`, `crawl_station_data`, `crawl_station_master_data`, and their helpers) into `src/etl/assets/hnd_bavaria.py`.
  - Remove the `argparse` logic and the main execution block (`if __name__ == '__main__':`).
  - Modify the functions to use the `httpx` library instead of `requests` for consistency with `pegelonline.py`.
  - Change the function return types from Pandas DataFrames to **Polars DataFrames** to align with the project's standard.

- **Action 1.3: Add New Dependencies**
  - Add `beautifulsoup4` to the `pyproject.toml` file to handle HTML parsing.

## 3. Phase 2: Create New Raw Data Assets

Next, we will create new Dagster assets that execute the refactored crawler logic and represent the raw, unprocessed data from the HND source.

- **Action 2.1: Define HND Master Data Asset**
  - In `src/etl/assets/hnd_bavaria.py`, define a new asset: `@asset(name="hnd_station_master_data_raw", group_name="hnd_bavaria_load")`.
  - This asset will call the refactored `crawl_station_master_data` function to fetch and return a single Polars DataFrame containing the master data for all Bavarian stations.

- **Action 2.2: Define HND Timeseries Asset**
  - In `src/etl/assets/hnd_bavaria.py`, define a second asset: `@asset(name="hnd_water_levels_raw", group_name="hnd_bavaria_load")`.
  - This asset will call the refactored `crawl_station_data` function and return a Polars DataFrame with the timeseries data (both measurements and forecasts).

## 4. Phase 3: Integrate Data into Existing Assets

This is the core integration phase, where the existing assets are modified to consume, transform, and merge the new HND data.

- **Action 3.1: Modify `station_data_parquet` Asset**
  1.  **Dependency**: Add `hnd_station_master_data_raw` as a dependency to the existing `station_data_parquet` asset in `src/etl/assets/pegelonline.py`.
  2.  **Load**: In the asset function, accept the HND master data DataFrame as an input.
  3.  **Transform**: Standardize the HND DataFrame. This includes renaming `Messstellen-Nr.` to `number` to serve as a common join key.
  4.  **Merge**: Perform an **outer join** between the Pegelonline stations DataFrame and the transformed HND stations DataFrame on the `number` column. An outer join ensures that stations existing in only one of the two sources are not lost.
  5.  **Coalesce**: For columns that exist in both datasets (e.g., `longname`, `longitude`, `latitude`), create a unified column by filling nulls in the Pegelonline data with values from the HND data. This enriches the dataset by filling in missing information.

- **Action 3.2: Modify `historic_timeseries_data` Asset**
  1.  **Dependency**: Add `hnd_water_levels_raw` and the modified `station_data_parquet` as dependencies.
  2.  **Load**: Accept the HND water levels DataFrame and the newly enriched station data (which contains the crucial `uuid`-to-`number` mapping) as inputs.
  3.  **Transform**: 
      - Filter the HND water levels data to select only measured values (`Type == 'measured'`).
      - Join with the station data on the station name to map each measurement to its corresponding `uuid`.
      - Rename and select columns (`DateTime` -> `timestamp`, `WaterLevel` -> `value`, `uuid`) to match the target schema.
  4.  **Concatenate**: Use `pl.concat` to append the transformed HND timeseries data to the timeseries data from the Pegelonline API.

- **Action 3.3: Modify `current_water_level` Asset**
  1.  This asset will be modified in a similar fashion to the historic one. It will take `hnd_water_levels_raw` and `station_data_parquet` as new inputs.
  2.  It will filter the HND data for the most recent measured value for each station, transform it to the target schema, and concatenate it with the data from the Pegelonline API.

- **Action 3.4: Handle Forecast Data**
  - **Challenge**: The HND crawler provides forecasts as a *range* (`Forecast_Lower`, `Forecast_Upper`), while the existing `forecasts.parquet` schema has a single `value` column. A direct merge is not possible without losing information or breaking the schema.
  - **Solution**: We will **not** merge the HND forecast data into the existing `forecasts.parquet` file. Instead, a new, separate asset will be created to handle it.
  - **New Asset**: Define `@asset(name="hnd_forecasts_parquet", group_name="hnd_bavaria_processed")` in `src/etl/assets/hnd_bavaria.py`. This asset will process the forecast data from `hnd_water_levels_raw` and save it to its own Parquet file (`processed/hnd_forecasts.parquet`) in the Hugging Face repo. This preserves the data integrity of both sources.

## 5. Phase 4: Update Pipeline Definitions

Finally, we will update the Dagster definitions to include the new assets and jobs.

- **Action 4.1: Update Definitions File**
  - In `src/etl/definitions.py`, import the new assets from `hnd_bavaria.py`.
  - Add the new assets to the `Definitions` list.
- **Action 4.2: Define New Job**
  - Create a new asset job named `hnd_bavaria_load` that targets the `hnd_bavaria_load` and `hnd_bavaria_processed` asset groups. This job can be run independently or scheduled as needed to refresh the Bavarian data.
