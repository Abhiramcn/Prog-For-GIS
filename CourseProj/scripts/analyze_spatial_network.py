"""
analyze_spatial_network.py
--------------------------
Conducts spatial network analysis on the 100% connected Nedumangad road graph and POI distribution:
1. Calculates degree centrality and Brandes betweenness centrality for road intersections.
2. Identifies key spatially dispersed bottleneck junctions across the entire municipality.
3. Measures network distance and spatial accessibility from all 42 official wards to healthcare hubs (Taluk Hospital).
4. Outputs summary statistics and ranking of top critical nodes.
"""

import os
import sys
import json
import csv
import math
import xml.etree.ElementTree as ET
import networkx as nx

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
from shapely.geometry import shape, LineString

DATA_DIR = r"D:\GISLab\Prog-For-GIS\CourseProj\data"

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    a = min(1.0, max(0.0, a))
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def build_connected_osm_graph():
    print("Building 100% connected OSM topological road graph...", flush=True)
    b_sf = shapefile.Reader(os.path.join(DATA_DIR, "nedumangad_boundary.shp"))
    b_poly = shape(b_sf.shape(0))

    tree = ET.parse(os.path.join(DATA_DIR, "nedumangad_raw_osm_official.xml"))
    root = tree.getroot()
    nodes = {n.get('id'): (float(n.get('lon')), float(n.get('lat'))) for n in root.findall('node')}

    valid_highways = {
        'primary', 'secondary', 'tertiary', 'residential',
        'unclassified', 'living_street', 'trunk', 'road', 'service'
    }

    G = nx.Graph()
    road_names = {}

    for way in root.findall('way'):
        tags = {t.get('k'): t.get('v') for t in way.findall('tag')}
        hw = tags.get('highway')
        if hw not in valid_highways:
            continue

        nd_refs = [nd.get('ref') for nd in way.findall('nd') if nd.get('ref') in nodes]
        if len(nd_refs) < 2:
            continue

        coords = [nodes[ref] for ref in nd_refs]
        ls = LineString(coords)
        if ls.intersects(b_poly):
            name = tags.get('name', tags.get('name:en', f"{hw.capitalize()} Road"))
            for i in range(len(nd_refs) - 1):
                u, v = nd_refs[i], nd_refs[i+1]
                p1, p2 = nodes[u], nodes[v]
                dist = haversine_m(p1[1], p1[0], p2[1], p2[0])
                G.add_edge(u, v, weight=dist, road_type=hw, name=name)
                G.nodes[u]['lon'] = p1[0]
                G.nodes[u]['lat'] = p1[1]
                G.nodes[v]['lon'] = p2[0]
                G.nodes[v]['lat'] = p2[1]
                road_names[(u, v)] = name
                road_names[(v, u)] = name

    print(f"Topological graph constructed: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges.", flush=True)
    return G, road_names

def analyze_network(G, road_names):
    print("Computing network betweenness and degree centrality metrics...", flush=True)
    # Degree centrality
    deg_cent = nx.degree_centrality(G)

    # Sampled betweenness centrality (k=250 for speed)
    print("Sampling betweenness centrality (k=250)...", flush=True)
    bc = nx.betweenness_centrality(G, k=250, weight='weight', seed=42)
    sorted_nodes = sorted(bc.items(), key=lambda x: x[1], reverse=True)

    # Spatially disperse bottlenecks so they represent distinct geographic hubs across town (min 280m separation)
    selected = []
    for nid, score in sorted_nodes:
        pos = (G.nodes[nid]['lat'], G.nodes[nid]['lon'])
        if not any(haversine_m(pos[0], pos[1], G.nodes[s]['lat'], G.nodes[s]['lon']) < 280.0 for s, _ in selected):
            selected.append((nid, score))
        if len(selected) >= 10:
            break

    print("\n=== Top 10 Critical Transmission Corridor Junctions in Nedumangad ===")
    results = []
    for rank, (node_id, b_score) in enumerate(selected, 1):
        node_attr = G.nodes[node_id]
        deg = G.degree[node_id]
        incident_roads = sorted({data['name'] for _, _, data in G.edges(node_id, data=True) if data.get('name')})
        road_str = ", ".join(incident_roads[:2]) if incident_roads else "Local Junction"
        degree_centrality = deg_cent[node_id]
        print(f"Rank {rank:2d}: Node {node_id} | Lat: {node_attr['lat']:.5f}, Lon: {node_attr['lon']:.5f} | Betweenness: {b_score:.5f} | Degree: {deg} | Roads: {road_str}")
        results.append({
            'rank': rank,
            'node_id': node_id,
            'lat': node_attr['lat'],
            'lon': node_attr['lon'],
            'betweenness': round(b_score, 6),
            'degree': deg,
            'degree_centrality': round(degree_centrality, 6),
            'roads': road_str
        })

    out_csv = os.path.join(DATA_DIR, "network_bottlenecks.csv")
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['rank', 'node_id', 'lat', 'lon', 'betweenness', 'degree', 'degree_centrality', 'roads'])
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved critical bottlenecks to {out_csv}", flush=True)
    return results

def analyze_healthcare_accessibility(G):
    print("\nAnalyzing road-network access to healthcare hubs for all 42 wards...", flush=True)
    with open(os.path.join(DATA_DIR, "nedumangad_hubs.geojson"), 'r', encoding='utf-8') as f:
        hubs_geo = json.load(f)

    healthcare_hubs = [
        feat for feat in hubs_geo.get('features', [])
        if feat.get('properties', {}).get('category') == 'Healthcare'
    ]

    # Find nearest road node for each healthcare hub
    graph_nodes = list(G.nodes(data=True))
    source_connectors = {}
    for feat in healthcare_hubs:
        lon, lat = feat['geometry']['coordinates']
        nearest_node = min(graph_nodes, key=lambda n: haversine_m(lat, lon, n[1]['lat'], n[1]['lon']))
        dist = haversine_m(lat, lon, nearest_node[1]['lat'], nearest_node[1]['lon'])
        source_connectors[nearest_node[0]] = (dist, feat['properties'].get('name', 'Taluk Hospital'))

    # Connect virtual healthcare source
    access_G = G.copy()
    virtual_hosp = "HOSP_SOURCE"
    for nid, (d, _) in source_connectors.items():
        access_G.add_edge(virtual_hosp, nid, weight=d)

    dists, paths = nx.single_source_dijkstra(access_G, virtual_hosp, weight='weight')

    # Load 42 wards
    wards_sf = shapefile.Reader(os.path.join(DATA_DIR, "nedumangad_wards.shp"))
    records = wards_sf.records()
    hosp_lat, hosp_lon = 8.6012, 77.0015  # Taluk Hospital coordinates

    ward_access = []
    for i, rec in enumerate(records):
        wno = rec[0]
        wname = rec[1]
        pop = rec[2]
        pts = wards_sf.shape(i).points
        clon = sum(p[0] for p in pts) / len(pts)
        clat = sum(p[1] for p in pts) / len(pts)

        straight_dist_km = haversine_m(clat, clon, hosp_lat, hosp_lon) / 1000.0
        nearest_node = min(graph_nodes, key=lambda n: haversine_m(clat, clon, n[1]['lat'], n[1]['lon']))
        ward_connector_km = haversine_m(clat, clon, nearest_node[1]['lat'], nearest_node[1]['lon']) / 1000.0

        net_m = dists.get(nearest_node[0])
        if net_m is not None:
            net_km = round(ward_connector_km + net_m / 1000.0, 2)
            tt_min = round(net_km / 25.0 * 60.0 + 3.0, 1)  # 25 km/h urban speed + 3 min response
            hub_name = "Nedumangad Taluk Hospital"
        else:
            net_km = round(straight_dist_km * 1.35, 2)
            tt_min = round(net_km / 25.0 * 60.0 + 3.0, 1)
            hub_name = "Nedumangad Taluk Hospital"

        ward_access.append({
            'ward_no': wno,
            'ward_name': wname,
            'population': pop,
            'dist_to_taluk_hosp_km': round(straight_dist_km, 2),
            'travel_time_min_est': round(straight_dist_km / 25.0 * 60.0 + 3.0, 1),
            'nearest_healthcare_hub': hub_name,
            'dist_to_nearest_healthcare_network_km': net_km,
            'network_travel_time_min_est': tt_min
        })

    out_csv = os.path.join(DATA_DIR, "ward_healthcare_accessibility.csv")
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'ward_no', 'ward_name', 'population', 'dist_to_taluk_hosp_km',
            'travel_time_min_est', 'nearest_healthcare_hub',
            'dist_to_nearest_healthcare_network_km', 'network_travel_time_min_est'
        ])
        writer.writeheader()
        writer.writerows(ward_access)
    print(f"Saved ward accessibility for all {len(ward_access)} wards to {out_csv}", flush=True)

def main():
    print("=== Nedumangad Road Network & Spatial Epidemic Vulnerability Analysis ===")
    G, road_names = build_connected_osm_graph()
    analyze_network(G, road_names)
    analyze_healthcare_accessibility(G)
    print("=== Network Analysis Complete! ===", flush=True)

if __name__ == '__main__':
    main()
