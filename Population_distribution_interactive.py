import geopandas as gpd
import pandas as pd
import osmnx as ox

# -----------------------------
# FILES
# -----------------------------
GRID_FILE = "Python/target_zones_grid250m_EPSG3067.geojson"

POP_WORK = "Python/HMA_Dynamic_population_24H_workdays.csv"
POP_SAT = "Python/HMA_Dynamic_population_24H_sat.csv"
POP_SUN = "Python/HMA_Dynamic_population_24H_sun.csv"

OUTPUT = "Python/helsinki_population.geojson"

# -----------------------------
# 1. LOAD GRID
# -----------------------------
grid = gpd.read_file(GRID_FILE)
grid = grid.set_crs(epsg=3067, allow_override=True)

# -----------------------------
# 2. LOAD POPULATION DATA
# -----------------------------
def load_pop(file, label):
    df = pd.read_csv(file)
    df["day_type"] = label
    return df

pop_all = pd.concat([
    load_pop(POP_WORK, "weekday"),
    load_pop(POP_SAT, "saturday"),
    load_pop(POP_SUN, "sunday"),
])

# -----------------------------
# 3. MERGE
# -----------------------------
merged = grid.merge(pop_all, on="YKR_ID")

# Fill missing values
hour_cols = [f"H{i}" for i in range(24)]
merged[hour_cols] = merged[hour_cols].fillna(0)

# -----------------------------
# 4. FIX GEOMETRY
# -----------------------------
merged = merged[merged.geometry.notnull()]
merged = merged[merged.is_valid]

# -----------------------------
# 5. CLIP TO HELSINKI
# -----------------------------
helsinki = ox.geocode_to_gdf("Helsinki, Finland")
helsinki = helsinki.to_crs(epsg=3067)

merged = gpd.clip(merged, helsinki)

# -----------------------------
# 6. SIMPLIFY GEOMETRY (IMPORTANT)
# -----------------------------
# Adjust tolerance if needed (10–30 is typical)
merged["geometry"] = merged["geometry"].simplify(15)

# -----------------------------
# 7. REDUCE COLUMNS (CRITICAL)
# -----------------------------
keep_cols = ["YKR_ID", "geometry", "day_type"] + hour_cols
merged = merged[keep_cols]

# -----------------------------
# 8. REPROJECT FOR WEB
# -----------------------------
merged = merged.to_crs(epsg=4326)

# -----------------------------
# 9. EXPORT
# -----------------------------
merged.to_file(OUTPUT, driver="GeoJSON")

print(f"Saved optimized GeoJSON: {OUTPUT}")
print(f"Number of features: {len(merged)}")