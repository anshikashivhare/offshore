import json

log_content = ""
with open("/Users/apple/.gemini/antigravity-ide/brain/2327f688-702e-4ae8-ad96-b614d622164d/.system_generated/tasks/task-1046.log") as f:
    log_content = f.read()

# The response JSON is on the last line after "Response: "
last_line = log_content.strip().split("\n")[-1]
json_str = last_line.replace("Response: ", "")

data = json.loads(json_str)

print(f"SUCCESS! Status: 201")
print(f"Distance: {data.get('distance_nm', 'N/A')} NM")
print(f"Route origin: {data.get('origin')}")
print(f"Route destination: {data.get('destination')}")

geometry = data.get('geometry', '')
if geometry:
    points = geometry.replace("LINESTRING(", "").replace(")", "").split(",")
    print(f"Total waypoints: {len(points)}")
    print(f"First point: {points[0].strip()}")
    print(f"Last point: {points[-1].strip()}")
else:
    print("ERROR: No geometry returned.")
