import os
path = '/Users/apple/.gemini/antigravity-ide/brain/8f308f7c-9f7b-4046-af22-cdbb0756ff8b/task.md'
with open(path, 'r') as f:
    content = f.read()
content = content.replace('[/] Create', '[x] Create')
content = content.replace('[ ] Create `backend/app/ws/routes.py`', '[x] Create `backend/app/ws/routes.py`')
content = content.replace('[ ] Update `backend/app/main.py`', '[x] Update `backend/app/main.py`')
with open(path, 'w') as f:
    f.write(content)
