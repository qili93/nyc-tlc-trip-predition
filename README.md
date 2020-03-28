# nyc-tlc-trip-predition
Demand forecast of New York City Taxi at Manhattan at 5min, 15min and 30min slot.

## PoC requirement

1. Use only the data after Y2018 (Jan to June) and Manhattan as the demo area.
2. Design a stream of simulated input, and forecast 5min/15min/30min’s demands.
3. Since the data is huge, you could just use yellow taxi part to do the work. And if you are not familiar with GIS systems, you could just use a description of grid (suggest 0.5 Mile * 0.5 Mile) to illustrate your result.

## Step 1. Data Preprocessing

Source of data to be download: https://www1.nyc.gov/site/tlc/about/tlc-trip-record-data.page

1. Run the script first to download the data:

   ```bash
   bash scripts/download_tlc_trip.sh ./data
   ```

2. Data Virtulization & Data Cleaning
   

3. D