import os, sys
try:
    os.add_dll_directory(r"C:\Program Files\QGIS 3.44.13\bin")
except Exception as e:
    print("add_dll_directory error:", e)

try:
    import geopandas as gpd
    print("geopandas version:", gpd.__version__)
except Exception as e:
    print("geopandas error:", e)

try:
    import networkx as nx
    print("networkx version:", nx.__version__)
except Exception as e:
    print("networkx error:", e)

try:
    import requests
    print("requests version:", requests.__version__)
except Exception as e:
    print("requests error:", e)
