import urllib.request
import json
import os

url = "https://raw.githubusercontent.com/tayljordan/ports/master/ports.json"
response = urllib.request.urlopen(url)
data = json.loads(response.read())
port_list = data.get("ports", [])

ports = []
for port in port_list:
    name = port.get("wpi_port_name") or port.get("point_of_interest") or "Unknown"
    if name == "Unknown" or not name:
        continue
    lat = port.get("latitude")
    lon = port.get("longitude")
    if lat is None or lon is None:
        continue
    
    ports.append({
        "name": name,
        "country": port.get("country", "Unknown"),
        "lat": lat,
        "lon": lon
    })

os.makedirs("backend/data", exist_ok=True)
with open("backend/data/ports.json", "w") as f:
    json.dump(ports, f)

print(f"Saved {len(ports)} ports to backend/data/ports.json")
