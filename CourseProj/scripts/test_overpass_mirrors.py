import urllib.request
import urllib.parse
import json
import time

mirrors = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass-api.de/api/interpreter"
]

def query_overpass_mirrors(query):
    data = urllib.parse.urlencode({'data': query}).encode('utf-8')
    headers = {'User-Agent': 'NedumangadEpidemicStudy/1.0 (contact@research.edu)'}
    for mirror in mirrors:
        print(f"Trying mirror: {mirror} ...")
        try:
            req = urllib.request.Request(mirror, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    print(f"Success with {mirror}!")
                    return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            print(f"  Failed {mirror}: {e}")
            time.sleep(1)
    return None

# Simple query for Nedumangad node or relation tags
query = """
[out:json][timeout:25];
(
  relation["name"~"Nedumangad"];
  node["place"]["name"="Nedumangad"];
);
out tags;
"""

res = query_overpass_mirrors(query)
if res:
    print(f"Got {len(res.get('elements', []))} elements:")
    for elem in res.get('elements', []):
        tags = elem.get('tags', {})
        print(f"- Type: {elem.get('type')}, ID: {elem.get('id')}, Name: {tags.get('name')}, Boundary: {tags.get('boundary')}, AdminLevel: {tags.get('admin_level')}, Place: {tags.get('place')}")
else:
    print("Could not query Overpass mirrors.")
