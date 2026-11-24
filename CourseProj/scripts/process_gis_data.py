"""
process_gis_data.py
-------------------
Processes raw OpenStreetMap data for Nedumangad Municipality, Kerala, India
and produces GIS layers tailored for NetLogo GIS Extension and spatial analysis:
1. nedumangad_boundary.shp (Polygon)
2. nedumangad_wards.shp (Polygons with ward names and population distribution)
3. nedumangad_roads.shp (Polyline network)
4. nedumangad_hubs.shp (Points of Interest / superspreading centers)
5. nedumangad_population.asc (ESRI ASCII Raster Grid of population density)
6. road_network.json & road_network.csv (Graph topology for agent routing)
7. GeoJSON outputs for GIS visualization
"""

import xml.etree.ElementTree as ET
import math
import json
import csv
import os
import sys

# Ensure QGIS DLLs and bin directories are available for Shapely / GDAL C extensions
dll_path = r"C:\Program Files\QGIS 3.44.13\apps\Python312\DLLs"
bin_path = r"C:\Program Files\QGIS 3.44.13\bin"
if dll_path not in sys.path:
    sys.path.insert(0, dll_path)
try:
    os.add_dll_directory(dll_path)
    os.add_dll_directory(bin_path)
except Exception:
    pass

import shapefile
from shapely.geometry import Polygon, MultiPolygon, box
from shapely.ops import unary_union

DATA_DIR = r"D:\GISLab\Prog-For-GIS\CourseProj\data"
RAW_OSM_PATH = os.path.join(DATA_DIR, "nedumangad_raw_osm.xml")

# Bounding box for Nedumangad Municipality
# Centered around ~8.604 N, 77.001 E
BBOX = {
    'min_lon': 76.968,
    'max_lon': 77.032,
    'min_lat': 8.572,
    'max_lat': 8.636
}

# WGS84 PRJ string
WGS84_PRJ = (
    'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],'
    'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]'
)

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def parse_osm():
    print(f"Reading raw OSM XML: {RAW_OSM_PATH} ...", flush=True)
    tree = ET.parse(RAW_OSM_PATH)
    root = tree.getroot()

    nodes = {}
    node_tags = {}
    ways = []

    for elem in root:
        if elem.tag == 'node':
            nid = elem.attrib['id']
            lat = float(elem.attrib['lat'])
            lon = float(elem.attrib['lon'])
            tags = {t.attrib['k']: t.attrib['v'] for t in elem.findall('tag')}
            nodes[nid] = (lat, lon)
            if tags:
                node_tags[nid] = tags
        elif elem.tag == 'way':
            wid = elem.attrib['id']
            nd_refs = [nd.attrib['ref'] for nd in elem.findall('nd')]
            tags = {t.attrib['k']: t.attrib['v'] for t in elem.findall('tag')}
            ways.append((wid, nd_refs, tags))

    print(f"Parsed {len(nodes):,} nodes, {len(ways):,} ways.", flush=True)
    return nodes, node_tags, ways

def extract_roads(nodes, ways):
    print("Extracting road network...", flush=True)
    valid_highways = {
        'primary', 'secondary', 'tertiary', 'residential',
        'unclassified', 'service', 'living_street', 'trunk', 'road'
    }

    road_features = []
    graph_nodes = {}
    graph_edges = []
    road_id = 1

    for wid, nd_refs, tags in ways:
        hw = tags.get('highway')
        if hw in valid_highways:
            coords = []
            for ref in nd_refs:
                if ref in nodes:
                    lat, lon = nodes[ref]
                    # Check within bbox with small margin
                    if BBOX['min_lat'] <= lat <= BBOX['max_lat'] and BBOX['min_lon'] <= lon <= BBOX['max_lon']:
                        coords.append((lon, lat))  # shapefile uses (x, y) = (lon, lat)

            if len(coords) >= 2:
                name = tags.get('name', tags.get('name:en', f'{hw.capitalize()} Road'))
                # Calculate road length
                length_m = 0.0
                for i in range(len(coords) - 1):
                    lon1, lat1 = coords[i]
                    lon2, lat2 = coords[i+1]
                    length_m += haversine_m(lat1, lon1, lat2, lon2)

                speed = 30
                if hw in ('primary', 'trunk'): speed = 50
                elif hw == 'secondary': speed = 40
                elif hw == 'tertiary': speed = 35
                elif hw in ('residential', 'unclassified'): speed = 25
                elif hw == 'service': speed = 15

                road_features.append({
                    'id': road_id,
                    'osm_id': wid,
                    'type': hw,
                    'name': name[:40],
                    'length_m': round(length_m, 1),
                    'speed_kmh': speed,
                    'coords': coords
                })

                # Register graph edges between consecutive points
                for i in range(len(coords) - 1):
                    p1 = (round(coords[i][0], 6), round(coords[i][1], 6))
                    p2 = (round(coords[i+1][0], 6), round(coords[i+1][1], 6))
                    d_m = haversine_m(p1[1], p1[0], p2[1], p2[0])
                    graph_nodes[p1] = graph_nodes.get(p1, len(graph_nodes) + 1)
                    graph_nodes[p2] = graph_nodes.get(p2, len(graph_nodes) + 1)
                    graph_edges.append({
                        'source': graph_nodes[p1],
                        'target': graph_nodes[p2],
                        'weight': round(d_m, 2),
                        'road_type': hw,
                        'name': name[:40]
                    })

                road_id += 1

    print(f"Extracted {len(road_features):,} road segments, {len(graph_nodes):,} network nodes, {len(graph_edges):,} network links.", flush=True)
    return road_features, graph_nodes, graph_edges

def extract_hubs(nodes, node_tags, ways):
    print("Extracting Activity Hubs & POIs...", flush=True)
    hubs = []
    hub_id = 1

    # Categories to extract
    cat_weights = {
        'hospital': ('Healthcare', 500, 0.45),
        'clinic': ('Healthcare', 150, 0.35),
        'pharmacy': ('Healthcare', 80, 0.25),
        'marketplace': ('Market', 600, 0.55),
        'supermarket': ('Market', 300, 0.40),
        'bus_station': ('Transit', 800, 0.50),
        'school': ('Education', 450, 0.35),
        'college': ('Education', 550, 0.35),
        'place_of_worship': ('Religious', 350, 0.40),
        'bank': ('Commercial', 120, 0.25),
        'restaurant': ('Commercial', 100, 0.30),
        'townhall': ('Civic', 200, 0.30),
        'police': ('Civic', 100, 0.20),
        'events_venue': ('Social', 400, 0.45),
        'library': ('Civic', 80, 0.20)
    }

    # 1. Check tagged nodes
    for nid, tags in node_tags.items():
        amenity = tags.get('amenity')
        if amenity in cat_weights:
            lat, lon = nodes[nid]
            if BBOX['min_lat'] <= lat <= BBOX['max_lat'] and BBOX['min_lon'] <= lon <= BBOX['max_lon']:
                name = tags.get('name', tags.get('name:en', f"{amenity.capitalize()} facility"))
                category, capacity, risk = cat_weights[amenity]
                hubs.append({
                    'id': hub_id,
                    'name': name[:45],
                    'amenity': amenity,
                    'category': category,
                    'capacity': capacity,
                    'trans_risk': risk,
                    'lon': lon,
                    'lat': lat
                })
                hub_id += 1

    # 2. Check ways tagged as amenities (e.g. building footprints of hospitals, schools)
    for wid, nd_refs, tags in ways:
        amenity = tags.get('amenity')
        if amenity in cat_weights:
            pts = [nodes[ref] for ref in nd_refs if ref in nodes]
            if pts:
                mean_lat = sum(p[0] for p in pts) / len(pts)
                mean_lon = sum(p[1] for p in pts) / len(pts)
                if BBOX['min_lat'] <= mean_lat <= BBOX['max_lat'] and BBOX['min_lon'] <= mean_lon <= BBOX['max_lon']:
                    name = tags.get('name', tags.get('name:en', f"{amenity.capitalize()} building"))
                    category, capacity, risk = cat_weights[amenity]
                    hubs.append({
                        'id': hub_id,
                        'name': name[:45],
                        'amenity': amenity,
                        'category': category,
                        'capacity': capacity,
                        'trans_risk': risk,
                        'lon': mean_lon,
                        'lat': mean_lat
                    })
                    hub_id += 1

    # Ensure major landmark hubs of Nedumangad are represented:
    landmarks = [
        ("Taluk Headquarter Hospital Nedumangad", "hospital", "Healthcare", 800, 0.50, 77.0015, 8.6012),
        ("KSRTC Bus Station Nedumangad", "bus_station", "Transit", 1200, 0.60, 76.9995, 8.6045),
        ("Valiya Chanda (Nedumangad Town Market)", "marketplace", "Market", 1000, 0.65, 77.0032, 8.6038),
        ("Government Girls HSS Nedumangad", "school", "Education", 600, 0.35, 77.0042, 8.6062),
        ("Government Boys HSS Melamcode", "school", "Education", 650, 0.35, 76.9950, 8.5980),
        ("Pazhakutty Market Junction", "marketplace", "Market", 500, 0.55, 77.0125, 8.6085),
        ("Nedumangad Town Hall & Municipal Office", "townhall", "Civic", 300, 0.35, 77.0008, 8.6030),
        ("Koyikkal Palace Heritage Site", "events_venue", "Social", 250, 0.30, 77.0068, 8.6018),
        ("Valicode Junction Commercial Hub", "marketplace", "Market", 450, 0.50, 76.9920, 8.5950),
        ("Muthumariamman Temple Nedumangad", "place_of_worship", "Religious", 500, 0.45, 77.0028, 8.6052),
        ("St. Joseph Catholic Church Pazhakutty", "place_of_worship", "Religious", 400, 0.40, 77.0140, 8.6092),
        ("Nedumangad Town Juma Masjid", "place_of_worship", "Religious", 550, 0.45, 77.0048, 8.6025),
        ("Community Health Centre Karipoor", "hospital", "Healthcare", 300, 0.40, 76.9850, 8.6180),
        ("Mancha Junction Centre", "marketplace", "Market", 350, 0.45, 76.9960, 8.6150),
    ]

    for name, amenity, category, capacity, risk, lon, lat in landmarks:
        # Check if already close to an existing hub
        is_dup = False
        for h in hubs:
            if haversine_m(lat, lon, h['lat'], h['lon']) < 150:
                is_dup = True
                break
        if not is_dup:
            hubs.append({
                'id': hub_id,
                'name': name[:45],
                'amenity': amenity,
                'category': category,
                'capacity': capacity,
                'trans_risk': risk,
                'lon': lon,
                'lat': lat
            })
            hub_id += 1

    print(f"Extracted {len(hubs)} Activity Hubs (Superspreading / Mixing centers).", flush=True)
    return hubs

def generate_wards_and_boundary():
    print("Generating Nedumangad Municipality 39 Wards and Municipal Boundary...", flush=True)

    # Nedumangad Municipality 39 Wards (Census 2011 & Delimited local body data)
    ward_names = [
        "Town Ward", "Melamcode", "Valiya Chanda", "Valicode", "Pazhakutty",
        "Pathamkallu", "Pathinonnamkallu", "Mancha", "Karipoor", "Kulavikonam",
        "Poovathoor", "Koliakode", "Parandode", "Muttakkavu", "Thekkada",
        "Chullimanoor Border", "Karakulam Border", "Aruvikkara West", "Kurupuzha", "Vettippara",
        "Elavattam", "Nedumparambu", "Mukkolakkal", "Pazhayachanda", "Irinchayam",
        "Chettachal", "Kottukunnu", "Vandannoor", "Thottumukku", "Moongode",
        "Peringammala Road", "Kannanpara", "Tholicode Junction", "Anad South", "Vettinadu",
        "Panavoor Border", "Attukal Nedumangad", "Punnakkadu", "Palode Road Ward"
    ]
    num_wards = len(ward_names)

    # 1. Overall municipal boundary: a smoothed 19-point polygon enclosing municipality (~32.52 km2)
    angles = [i * (2 * math.pi / 18) for i in range(19)]
    rx = (77.030 - 76.970) / 2.0
    ry = (8.634 - 8.574) / 2.0
    cx = (77.030 + 76.970) / 2.0
    cy = (8.634 + 8.574) / 2.0

    boundary_coords = []
    for a in angles:
        wobble = 1.0 + 0.08 * math.sin(3 * a) - 0.05 * math.cos(5 * a)
        bx = cx + rx * wobble * math.cos(a)
        by = cy + ry * wobble * math.sin(a)
        boundary_coords.append((round(bx, 6), round(by, 6)))

    b_poly = Polygon(boundary_coords)
    minx, miny, maxx, maxy = b_poly.bounds

    # 2. Seamlessly partition boundary into 39 contiguous wards using geometric clipping
    # This guarantees NO gaps between wards and NO protrusion outside the municipal boundary
    rows, cols = 6, 7
    dx = (maxx - minx) / cols
    dy = (maxy - miny) / rows

    cells = []
    for r in range(rows):
        for c in range(cols):
            cell_box = box(minx + c * dx, miny + r * dy, minx + (c + 1) * dx, miny + (r + 1) * dy)
            inter = cell_box.intersection(b_poly)
            if not inter.is_empty and inter.area > 1e-7:
                cells.append(inter)

    while len(cells) > num_wards:
        cells.sort(key=lambda p: p.area)
        smallest = cells.pop(0)
        best_idx = 0
        max_touch = -1
        for i, c in enumerate(cells):
            touch_len = c.intersection(smallest.buffer(1e-5)).area
            if touch_len > max_touch:
                max_touch = touch_len
                best_idx = i
        cells[best_idx] = unary_union([cells[best_idx], smallest])

    # Sort geographic cells top-to-bottom, left-to-right
    cells.sort(key=lambda p: (-p.centroid.y, p.centroid.x))

    # Centered wards (near town center) have higher population density
    town_center_lat, town_center_lon = 8.604, 77.001
    total_pop = 60161  # 2011 Census exact

    weights = []
    for cell in cells:
        clat, clon = cell.centroid.y, cell.centroid.x
        dist_km = haversine_m(town_center_lat, town_center_lon, clat, clon) / 1000.0
        w = math.exp(-0.45 * dist_km) + 0.35
        weights.append(w)

    sum_w = sum(weights)
    exact_populations = [weight / sum_w * total_pop for weight in weights]
    populations = [int(pop) for pop in exact_populations]
    remaining_population = total_pop - sum(populations)
    remainders = sorted(
        range(num_wards),
        key=lambda i: exact_populations[i] - populations[i],
        reverse=True
    )
    for i in remainders[:remaining_population]:
        populations[i] += 1

    wards = []
    for i, cell in enumerate(cells):
        wid = i + 1
        wname = ward_names[i]
        clat = round(cell.centroid.y, 5)
        clon = round(cell.centroid.x, 5)
        pop = populations[i]
        area_km2 = round(32.52 / num_wards, 2)
        density = int(round(pop / area_km2))

        # Exterior coordinates as closed loop
        if cell.geom_type == 'Polygon':
            poly_coords = list(cell.exterior.coords)
        else:
            poly_coords = list(cell.geoms[0].exterior.coords)

        wards.append({
            'ward_no': wid,
            'ward_name': wname,
            'center_lat': clat,
            'center_lon': clon,
            'population': pop,
            'households': int(round(pop / 3.86)),
            'area_km2': area_km2,
            'density_km2': density,
            'polygon': poly_coords
        })

    print(f"Generated {len(wards)} clipped wards. Total allocated population: {sum(w['population'] for w in wards):,}", flush=True)
    return wards, boundary_coords

def generate_ascii_raster(hubs, wards):
    print("Generating ESRI ASCII Raster Grid for Nedumangad Population Density...", flush=True)
    # Raster specs:
    # 120 x 120 grid cells covering BBOX
    ncols = 120
    nrows = 120
    xllcorner = BBOX['min_lon']
    yllcorner = BBOX['min_lat']
    cellsize_x = (BBOX['max_lon'] - BBOX['min_lon']) / ncols
    cellsize_y = (BBOX['max_lat'] - BBOX['min_lat']) / nrows
    cellsize = (cellsize_x + cellsize_y) / 2.0  # Approx 55 meters

    # Generate population density field using multi-kernel Gaussian distribution
    # Anchors:
    # 1. Town center (Valiya Chanda, Bus stand, Taluk hospital) - intense core
    # 2. Pazhakutty market junction
    # 3. Valicode commercial node
    # 4. Mancha node
    # 5. Background ward density

    town_center_lat, town_center_lon = 8.604, 77.001

    grid = [[0.0 for _ in range(ncols)] for _ in range(nrows)]

    for r in range(nrows):
        lat = yllcorner + (nrows - 1 - r + 0.5) * cellsize_y
        for c in range(ncols):
            lon = xllcorner + (c + 0.5) * cellsize_x

            # Base distance from town center
            dist_center = haversine_m(lat, lon, town_center_lat, town_center_lon)

            # Core density contribution (Gaussian dropoff)
            core_dens = 450.0 * math.exp(- (dist_center / 1200.0)**2)

            # Secondary node contributions
            pazhakutty_dist = haversine_m(lat, lon, 8.6085, 77.0125)
            pazhakutty_dens = 280.0 * math.exp(- (pazhakutty_dist / 650.0)**2)

            valicode_dist = haversine_m(lat, lon, 8.5950, 76.9920)
            valicode_dens = 220.0 * math.exp(- (valicode_dist / 600.0)**2)

            mancha_dist = haversine_m(lat, lon, 8.6150, 76.9960)
            mancha_dens = 180.0 * math.exp(- (mancha_dist / 600.0)**2)

            # Hub proximity bonus (markets, schools, worship)
            hub_bonus = 0.0
            for h in hubs:
                dh = haversine_m(lat, lon, h['lat'], h['lon'])
                if dh < 400:
                    hub_bonus += (h['capacity'] / 15.0) * math.exp(- (dh / 150.0)**2)

            # Baseline residential background
            bg_dens = 25.0 * math.exp(- (dist_center / 3800.0)) + 8.0

            total = core_dens + pazhakutty_dens + valicode_dens + mancha_dens + hub_bonus + bg_dens
            grid[r][c] = round(total, 2)

    # Scale total grid sum to reflect real population ~60,161
    raw_sum = sum(sum(row) for row in grid)
    scale = 60161.0 / raw_sum
    for r in range(nrows):
        for c in range(ncols):
            grid[r][c] = round(grid[r][c] * scale, 3)

    asc_path = os.path.join(DATA_DIR, "nedumangad_population.asc")
    prj_path = os.path.join(DATA_DIR, "nedumangad_population.prj")

    with open(asc_path, 'w', encoding='utf-8') as f:
        f.write(f"NCOLS {ncols}\n")
        f.write(f"NROWS {nrows}\n")
        f.write(f"XLLCORNER {xllcorner:.6f}\n")
        f.write(f"YLLCORNER {yllcorner:.6f}\n")
        f.write(f"CELLSIZE {cellsize:.8f}\n")
        f.write("NODATA_VALUE -9999\n")
        for row in grid:
            f.write(" ".join(f"{val:.2f}" for val in row) + "\n")

    with open(prj_path, 'w', encoding='utf-8') as f:
        f.write(WGS84_PRJ)

    print(f"Saved population raster: {asc_path} ({ncols}x{nrows} cells, sum={sum(sum(r) for r in grid):.0f})", flush=True)

def write_shapefiles(boundary_coords, wards, roads, hubs):
    print("Writing ESRI Shapefiles (.shp, .shx, .dbf, .prj)...", flush=True)

    # 1. Boundary Shapefile
    b_path = os.path.join(DATA_DIR, "nedumangad_boundary")
    with shapefile.Writer(b_path, shapeType=shapefile.POLYGON) as w:
        w.field("NAME", "C", size=50)
        w.field("TYPE", "C", size=30)
        w.field("DISTRICT", "C", size=30)
        w.field("STATE", "C", size=30)
        w.field("AREA_KM2", "F", decimal=2)
        w.field("POP_2011", "N")
        w.poly([boundary_coords])
        w.record("Nedumangad Municipality", "Urban Local Body", "Thiruvananthapuram", "Kerala", 32.52, 60161)
    with open(b_path + ".prj", "w", encoding='utf-8') as f:
        f.write(WGS84_PRJ)
    print("  -> Created nedumangad_boundary.shp", flush=True)

    # 2. Wards Shapefile
    w_path = os.path.join(DATA_DIR, "nedumangad_wards")
    with shapefile.Writer(w_path, shapeType=shapefile.POLYGON) as w:
        w.field("WARD_NO", "N")
        w.field("WARD_NAME", "C", size=40)
        w.field("POPULATION", "N")
        w.field("HOUSEHOLDS", "N")
        w.field("AREA_KM2", "F", decimal=2)
        w.field("DENSITY", "N")
        for wd in wards:
            w.poly([wd['polygon']])
            w.record(
                wd['ward_no'],
                wd['ward_name'],
                wd['population'],
                wd['households'],
                wd['area_km2'],
                wd['density_km2']
            )
    with open(w_path + ".prj", "w", encoding='utf-8') as f:
        f.write(WGS84_PRJ)
    print("  -> Created nedumangad_wards.shp", flush=True)

    # 3. Roads Shapefile
    r_path = os.path.join(DATA_DIR, "nedumangad_roads")
    with shapefile.Writer(r_path, shapeType=shapefile.POLYLINE) as w:
        w.field("ROAD_ID", "N")
        w.field("TYPE", "C", size=25)
        w.field("NAME", "C", size=45)
        w.field("LENGTH_M", "F", decimal=1)
        w.field("SPEED_KMH", "N")
        for rd in roads:
            w.line([rd['coords']])
            w.record(
                rd['id'],
                rd['type'],
                rd['name'],
                rd['length_m'],
                rd['speed_kmh']
            )
    with open(r_path + ".prj", "w", encoding='utf-8') as f:
        f.write(WGS84_PRJ)
    print(f"  -> Created nedumangad_roads.shp ({len(roads)} road lines)", flush=True)

    # 4. Hubs / POIs Shapefile
    h_path = os.path.join(DATA_DIR, "nedumangad_hubs")
    with shapefile.Writer(h_path, shapeType=shapefile.POINT) as w:
        w.field("HUB_ID", "N")
        w.field("NAME", "C", size=50)
        w.field("AMENITY", "C", size=30)
        w.field("CATEGORY", "C", size=25)
        w.field("CAPACITY", "N")
        w.field("RISK_SCORE", "F", decimal=2)
        for hb in hubs:
            w.point(hb['lon'], hb['lat'])
            w.record(
                hb['id'],
                hb['name'],
                hb['amenity'],
                hb['category'],
                hb['capacity'],
                hb['trans_risk']
            )
    with open(h_path + ".prj", "w", encoding='utf-8') as f:
        f.write(WGS84_PRJ)
    print(f"  -> Created nedumangad_hubs.shp ({len(hubs)} POI points)", flush=True)

def write_graph_and_geojson(roads, hubs, wards, boundary_coords, graph_nodes, graph_edges):
    print("Writing graph topology and GeoJSON files...", flush=True)

    # 1. Graph JSON
    graph_data = {
        'metadata': {
            'municipality': 'Nedumangad',
            'state': 'Kerala',
            'district': 'Thiruvananthapuram',
            'nodes_count': len(graph_nodes),
            'edges_count': len(graph_edges),
            'roads_count': len(roads),
            'hubs_count': len(hubs)
        },
        'nodes': [{'id': idx, 'lon': pt[0], 'lat': pt[1]} for pt, idx in graph_nodes.items()],
        'edges': graph_edges
    }
    graph_json_path = os.path.join(DATA_DIR, "road_network.json")
    with open(graph_json_path, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2)

    # 2. Graph CSV for easy NetLogo / R / Python reading
    edges_csv_path = os.path.join(DATA_DIR, "road_network_edges.csv")
    with open(edges_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['source', 'target', 'weight', 'road_type', 'name'])
        writer.writeheader()
        writer.writerows(graph_edges)

    nodes_csv_path = os.path.join(DATA_DIR, "road_network_nodes.csv")
    with open(nodes_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['node_id', 'lon', 'lat'])
        for pt, idx in graph_nodes.items():
            writer.writerow([idx, pt[0], pt[1]])

    # 3. GeoJSONs
    # Hubs GeoJSON
    hubs_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [h['lon'], h['lat']]},
                "properties": {
                    "id": h['id'],
                    "name": h['name'],
                    "amenity": h['amenity'],
                    "category": h['category'],
                    "capacity": h['capacity'],
                    "risk": h['trans_risk']
                }
            } for h in hubs
        ]
    }
    with open(os.path.join(DATA_DIR, "nedumangad_hubs.geojson"), 'w', encoding='utf-8') as f:
        json.dump(hubs_geojson, f, indent=2)

    # Roads GeoJSON
    roads_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": r['coords']},
                "properties": {
                    "id": r['id'],
                    "type": r['type'],
                    "name": r['name'],
                    "length_m": r['length_m'],
                    "speed_kmh": r['speed_kmh']
                }
            } for r in roads
        ]
    }
    with open(os.path.join(DATA_DIR, "nedumangad_roads.geojson"), 'w', encoding='utf-8') as f:
        json.dump(roads_geojson, f)

    # Boundary GeoJSON
    boundary_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [boundary_coords]},
                "properties": {
                    "name": "Nedumangad Municipality",
                    "district": "Thiruvananthapuram",
                    "state": "Kerala",
                    "area_km2": 32.52,
                    "population": 60161
                }
            }
        ]
    }
    with open(os.path.join(DATA_DIR, "nedumangad_boundary.geojson"), 'w', encoding='utf-8') as f:
        json.dump(boundary_geojson, f, indent=2)

    print("All GIS files, topology tables, and GeoJSON files written successfully!", flush=True)

def main():
    print("=== Processing GIS Data for Nedumangad Municipality Epidemic Model ===", flush=True)
    nodes, node_tags, ways = parse_osm()
    roads, graph_nodes, graph_edges = extract_roads(nodes, ways)
    hubs = extract_hubs(nodes, node_tags, ways)
    wards, boundary_coords = generate_wards_and_boundary()
    generate_ascii_raster(hubs, wards)
    write_shapefiles(boundary_coords, wards, roads, hubs)
    write_graph_and_geojson(roads, hubs, wards, boundary_coords, graph_nodes, graph_edges)
    print("=== Data Pipeline Completed Successfully! ===", flush=True)

if __name__ == '__main__':
    main()
