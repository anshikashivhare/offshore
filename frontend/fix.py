import os

def replace_in_file(path, old, new):
    if not os.path.exists(path):
        return
    with open(path, 'r') as f:
        content = f.read()
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)

p = "src/components/map/route-panel.tsx"
replace_in_file(p, 'setOrigin(-45, -60);', 'setOrigin({ lat: -60, lon: -45 });')
replace_in_file(p, 'setDestination(-45, -60);', 'setDestination({ lat: -60, lon: -45 });')

