import json

log_content = ""
with open("/Users/apple/.gemini/antigravity-ide/brain/2327f688-702e-4ae8-ad96-b614d622164d/.system_generated/tasks/task-1046.log") as f:
    log_content = f.read()

# The response JSON is on the last line after "Response: "
last_line = log_content.strip().split("\n")[-1]
json_str = last_line.replace("Response: ", "")

data = json.loads(json_str)

print("Keys:", data.keys())
print("Id:", data.get("id"))
print("Geometry type:", type(data.get("geometry")))
if isinstance(data.get("geometry"), dict):
    print("Geometry coordinates length:", len(data["geometry"].get("coordinates", [])))
    print("First coordinate:", data["geometry"]["coordinates"][0])
    print("Last coordinate:", data["geometry"]["coordinates"][-1])
