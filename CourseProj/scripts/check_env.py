import sys
print(f"Python: {sys.executable}")
modules = ['requests', 'shapely', 'geopandas', 'pyproj', 'networkx', 'matplotlib', 'numpy', 'scipy', 'osgeo']
for m in modules:
    try:
        __import__(m)
        print(f"  {m}: AVAILABLE")
    except Exception as e:
        print(f"  {m}: NOT AVAILABLE ({e})")
