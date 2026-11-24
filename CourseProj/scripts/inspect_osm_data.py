import xml.etree.ElementTree as ET
from collections import Counter
import os

xml_file = r"D:\GISLab\Prog-For-GIS\CourseProj\data\nedumangad_raw_osm.xml"

print("Parsing OSM XML data...", flush=True)
tree = ET.parse(xml_file)
root = tree.getroot()

nodes = {}
ways = []
relations = []

highway_counts = Counter()
amenity_counts = Counter()
building_counts = Counter()

amenity_list = []

for elem in root:
    if elem.tag == 'node':
        nid = elem.attrib['id']
        lat = float(elem.attrib['lat'])
        lon = float(elem.attrib['lon'])
        tags = {t.attrib['k']: t.attrib['v'] for t in elem.findall('tag')}
        nodes[nid] = (lat, lon)
        if 'amenity' in tags:
            amenity_counts[tags['amenity']] += 1
            amenity_list.append({
                'type': 'node',
                'id': nid,
                'name': tags.get('name', 'Unnamed'),
                'amenity': tags['amenity'],
                'lat': lat,
                'lon': lon
            })
    elif elem.tag == 'way':
        wid = elem.attrib['id']
        nd_refs = [nd.attrib['ref'] for nd in elem.findall('nd')]
        tags = {t.attrib['k']: t.attrib['v'] for t in elem.findall('tag')}
        ways.append((wid, nd_refs, tags))
        if 'highway' in tags:
            highway_counts[tags['highway']] += 1
        if 'amenity' in tags:
            amenity_counts[tags['amenity']] += 1
        if 'building' in tags:
            building_counts[tags['building']] += 1
    elif elem.tag == 'relation':
        relations.append(elem.attrib['id'])

print(f"Total Nodes: {len(nodes):,}")
print(f"Total Ways: {len(ways):,}")
print(f"Total Relations: {len(relations):,}")
print("\nTop Highway Types:")
for hw, count in highway_counts.most_common(12):
    print(f"  {hw:20s}: {count:5d}")

print("\nTop Amenity Types (Hubs / POIs):")
for am, count in amenity_counts.most_common(15):
    print(f"  {am:20s}: {count:5d}")

print("\nBuilding Count:", sum(building_counts.values()))
