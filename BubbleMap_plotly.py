import pandas as pd
import plotly.express as px
from pathlib import Path

data_dir = Path("Python/Bike_routes")

trip_files = sorted(data_dir.glob("2023-*.csv"))
station_file = data_dir / "HSL_bike_stations.csv"

trips = pd.concat(
    (pd.read_csv(file) for file in trip_files),
    ignore_index=True
)

trips.columns = trips.columns.str.strip()

trips["Departure"] = pd.to_datetime(trips["Departure"], errors="coerce")
trips["Return"] = pd.to_datetime(trips["Return"], errors="coerce")

trips = trips.dropna(
    subset=["Departure", "Departure station id", "Return station id"]
)

trips["Departure station id"] = trips["Departure station id"].astype(int)
trips["Return station id"] = trips["Return station id"].astype(int)

trips["date"] = trips["Departure"].dt.date

stations = pd.read_csv(station_file)
stations.columns = stations.columns.str.strip()
stations["ID"] = stations["ID"].astype(int)

departures = (
    trips.groupby(["date", "Departure station id"])
    .size()
    .reset_index(name="Average Daily Departures")
    .rename(columns={"Departure station id": "ID"})
)

returns = (
    trips.groupby(["date", "Return station id"])
    .size()
    .reset_index(name="Average Daily Returns")
    .rename(columns={"Return station id": "ID"})
)

daily_activity = (
    departures.merge(returns, on=["date", "ID"], how="outer")
    .fillna(0)
)

daily_activity["Average Daily Total Activity"] = (
    daily_activity["Average Daily Departures"]
    + daily_activity["Average Daily Returns"]
)

station_activity = (
    daily_activity.groupby("ID", as_index=False)
    .mean(numeric_only=True)
)

map_data = stations.merge(station_activity, on="ID", how="left").fillna(0)

map_data.to_csv("station_average_daily_activity.csv", index=False)

fig = px.scatter_map(
    map_data,
    lat="y",
    lon="x",
    size="Average Daily Total Activity",
    color="Average Daily Total Activity",
    color_continuous_scale="Tealgrn",
    hover_name="Name",
    hover_data={
        "Average Daily Departures": ":.1f",
        "Average Daily Returns": ":.1f",
        "Average Daily Total Activity": ":.1f",
        "x": False,
        "y": False
    },
    size_max=60,
    zoom=11,
    height=1000,
    title="Average Daily Bike Station Activity Helsinki and Vantaa, April–October 2023"
)

fig.update_traces(marker={"opacity": 0.7})

fig.update_layout(
    mapbox_style="carto-darkmatter",
    margin={"r": 0, "t": 60, "l": 0, "b": 0},
    showlegend=False
)

fig.write_html("interactive_bubble_map_station_activity.html", auto_open=True)
fig.show()