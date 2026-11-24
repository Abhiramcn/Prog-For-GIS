import urllib.request
import urllib.parse
import json
import sys

def query_overpass(query):
    url = "https://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({'data': query}).encode('utf-8')
    headers = {'User-Agent': 'NedumangadGISResearch/1.0 (sathv@research.org)'}
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode('utf-8'))

# Let's find administrative boundaries around Nedumangad
query = """
[out:json][timeout:60];
(
  relation["name"~"Nedumangad"]["boundary"="administrative"];
  relation["name:en"~"Nedumangad"]["boundary"="administrative"];
  node["place"~"town|city"]["name"="Nedumangad"];
);
out body;
>;
out skel qt;
"""

print("Querying Overpass for Nedumangad administrative boundaries and place node...")
try:
    res = query_overpass(query)
    print(f"Received {len(res.get('elements', []))} elements.")
    for elem in res.get('elements', []):
        if elem.get('type') in ('relation', 'node') and 'tags' in elem:
            tags = elem['tags']
            print(f"- Type: {elem['type']}, ID: {elem['id']}, Name: {tags.get('name')}, Admin Level: {tags.get('admin_level')}, Place: {tags.get('place')}, Tags: {list(tags.keys())[:8]}")
            if elem['type'] == 'node':
                print(f"  Lat: {elem.get('lat')}, Lon: {elem.get('lon')}")
except Exception as e:
    print(f"Error querying Overpass: {e}")
