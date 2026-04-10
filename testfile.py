# build_mixed_dataset.py
# requirements: pandas, requests, geopandas, shapely, rasterio (optional) - see README notes
import pandas as pd
import requests
import json
import math
from pathlib import Path

IN_FILE = "Rwa_AHS_2020_Section_2.2.csv"   # or .dta; if .dta use pandas.read_stata
OUT_FILE = "ahs_mixed_dataset.csv"
out = Path(OUT_FILE)

# 1. load microdata
try:
    df = pd.read_csv(IN_FILE)
except Exception:
    df = pd.read_stata(IN_FILE)  # try .dta

# 2. basic crop flags from s2q15_1..10 (the microdata uses numeric codes for crop types)
crop_cols = [f"s2q15_{i}" for i in range(1,11)]
# placeholder mapping: you should replace this with the official mapping from the data dictionary
crop_code_map = {
    1: "maize", 2: "millet", 3: "sorghum", 4: "rice", 5: "beans", 6: "peas",
    7: "irish_potato", 8: "sweet_potato", 9: "cassava", 10: "bananas",
    # ... extend according to codebook
}

# create one-hot flags
for code, crop in crop_code_map.items():
    df[f"grew_{crop}"] = 0
for c in crop_cols:
    if c in df.columns:
        df[c] = df[c].fillna(0).astype(int)
        for code, crop in crop_code_map.items():
            df.loc[df[c] == code, f"grew_{crop}"] = 1

# input & practice flags
df["used_improved_seed"] = df.get("s2q19", 0).fillna(0).apply(lambda x: 1 if x==1 else 0)
df["used_organic_fert"] = df.get("s2q22", 0).fillna(0).apply(lambda x: 1 if x==1 else 0)
df["used_inorg_fert"] = df.get("s2q23", 0).fillna(0).apply(lambda x: 1 if x==1 else 0)
df["used_pesticide"] = df.get("s2q26", 0).fillna(0).apply(lambda x: 1 if x==1 else 0)
df["used_irrigation"] = df.get("s2q30", 0).fillna(0).apply(lambda x: 1 if x==1 else 0)
df["soil_measures_count"] = df.get("measures_n", 0).fillna(0).astype(int)

# 3. attach district-level centroids (we'll need to supply a CSV with district centroids)
# prepare a CSV 'rwanda_district_centroids.csv' with columns: district_name, lat, lon
centroids = pd.read_csv("rwanda_district_centroids.csv")  # you can generate or I can provide
# merge by district name - adjust column names as needed
df = df.merge(centroids, left_on="s0q2", right_on="district_name", how="left")

# 4. sample SoilGrids for each unique lat/lon
def sample_soil(lon, lat):
    # SoilGrids REST API
    url = f"https://rest.soilgrids.org/query?lat={lat}&lon={lon}"
    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        return {}
    j = r.json()
    # parse a few variables (example: phh2o, soc, n)
    out = {}
    try:
        out["phh2o_mean"] = j["properties"]["phh2o"]["mean"]["0-5cm"]
    except:
        out["phh2o_mean"] = None
    try:
        out["soc_mean"] = j["properties"]["soc"]["mean"]["0-5cm"]
    except:
        out["soc_mean"] = None
    return out

# sample for unique district centroids
unique_centroids = df[["lat","lon"]].drop_duplicates().dropna()
soil_rows = []
for _, r in unique_centroids.iterrows():
    s = sample_soil(r["lon"], r["lat"])
    s["lat"] = r["lat"]; s["lon"] = r["lon"]
    soil_rows.append(s)
soildf = pd.DataFrame(soil_rows)
df = df.merge(soildf, on=["lat","lon"], how="left")

# 5. climate: fetching seasonal rainfall/temperature — this depends on source.
# Option A: if you have Meteo Rwanda ENACTS rasters, use rasterio and sample over the polygons.
# Option B: use CHIRPS (daily rainfall) via ftp; else use xarray to open the netcdf and compute seasonal totals.
# (Code for climate is left as a reproducible placeholder — I can fill it for you depending on which data you want.)

# 6. save merged CSV
df.to_csv(out, index=False)
print("Saved merged dataset to", out)