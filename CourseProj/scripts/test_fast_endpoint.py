import urllib.request
import urllib.parse
import json

endpoints = [
    ("Overpass main", "https://overpass-api.de/api/interpreter"),
    ("Overpass kumi", "https://overpass.kumi.systems/api/interpreter"),
    ("Overpass private coffee", "https://overpass.private.coffee/api/interpreter"),
    ("Nominatim search", "https://nominatim.openstreetmap.org/search?format=json&q=Nedumangad")
]

for name, url in endpoints:
    print(f"Testing {name}...", flush=True)
    try:
        if "overpass" in url:
            data = urllib.parse.urlencode({'data': '[out:json];node(around:1000,8.605,77.003)["amenity"="hospital"];out;'}).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'User-Agent': 'NedumangadTest/1.0'})
        else:
            req = urllib.request.Request(url, headers={'User-Agent': 'NedumangadTest/1.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            print(f"  -> {name} SUCCESS, status {resp.status}", flush=True)
            raw = resp.read()
            print(f"  -> received {len(raw)} bytes", flush=True)
            break
    except Exception as e:
        print(f"  -> {name} FAILED: {e}", flush=True)
