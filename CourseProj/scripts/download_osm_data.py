import urllib.request

bbox = "76.965,8.570,77.035,8.635"
url = f"https://api.openstreetmap.org/api/0.6/map?bbox={bbox}"
out_path = r"D:\GISLab\Prog-For-GIS\CourseProj\data\nedumangad_raw_osm.xml"

print(f"Downloading OSM data for bounding box {bbox}...", flush=True)
req = urllib.request.Request(url, headers={'User-Agent': 'NedumangadEpidemicStudy/1.0 (sathv@research.org)'})
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        content = resp.read()
        print(f"Downloaded {len(content):,} bytes ({len(content)/1024/1024:.2f} MB)", flush=True)
        with open(out_path, "wb") as f:
            f.write(content)
        print(f"Saved to {out_path}", flush=True)
except Exception as e:
    print(f"Download failed: {e}", flush=True)
    raise
