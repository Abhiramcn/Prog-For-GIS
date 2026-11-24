
"""3. Explore the given data (print results like count of forests from LULC data, Primary 
road names from road data etc. It can be of your choice) and print the area of 
Nedumangad """

import os
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point, box
import numpy as np

data_dir = os.path.join(
    os.path.dirname(__file__),
    "MTech26",
    "lab 6",
    "nedumangad_extracted",
    "nedumangad",
)

lulc = gpd.read_file(os.path.join(data_dir, "landuse", "nedumangad_landuse.shp"))
roads = gpd.read_file(os.path.join(data_dir, "roads", "nedumangad_road.shp"))
boundary = gpd.read_file(os.path.join(data_dir, "nedumangad_boundary.shp"))

print("Landuse columns:", lulc.columns.tolist())
print("Road columns:", roads.columns.tolist())
print("Boundary columns:", boundary.columns.tolist())

forest = lulc[lulc["fclass"].str.contains("forest", case=False, na=False)]

print("Total number of forest features:", len(forest))


print("\nPrimary road names:")
primary_roads = roads[roads["fclass"] == "primary"]
print(primary_roads["name"].dropna().unique()[:10])


boundary_projected = boundary.to_crs(epsg=32643)
area_km2 = boundary_projected.geometry.area.sum() / 1_000_000

print("\nArea of Nedumangad:", round(area_km2, 3), "sq. km")
