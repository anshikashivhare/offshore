import os
import platform
import subprocess
import json
from pathlib import Path

data = {}

# Phase 1: Machine Identity
data['machine'] = {
    'arch': platform.machine(),
    'os_version': platform.mac_ver()[0],
    'python_version': platform.python_version()
}

# Phase 2: Hardware Resources
import psutil
data['hardware'] = {
    'logical_cpus': psutil.cpu_count(logical=True),
    'physical_cpus': psutil.cpu_count(logical=False),
    'total_ram_gb': psutil.virtual_memory().total / (1024**3),
    'available_ram_gb': psutil.virtual_memory().available / (1024**3),
    'free_disk_gb': psutil.disk_usage('/').free / (1024**3)
}

try:
    cpu_model = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string']).decode('utf-8').strip()
except Exception:
    cpu_model = "Unknown"
data['hardware']['cpu_model'] = cpu_model

# Phase 3: ML Runtime
data['runtime'] = {}
try:
    import xgboost as xgb
    data['runtime']['xgboost'] = xgb.__version__
except ImportError:
    data['runtime']['xgboost'] = None

try:
    import torch
    data['runtime']['pytorch'] = torch.__version__
    data['runtime']['mps_built'] = torch.backends.mps.is_built() if hasattr(torch.backends, 'mps') else False
    data['runtime']['mps_available'] = torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False
except ImportError:
    data['runtime']['pytorch'] = None
    data['runtime']['mps_built'] = False
    data['runtime']['mps_available'] = False

# Phase 4: Dataset Inventory
import pandas as pd
datasets = []
data_dir = Path("ml/data/raw")
for file in data_dir.glob("*.csv"):
    size_mb = file.stat().st_size / (1024**2)
    try:
        rows = int(subprocess.check_output(['wc', '-l', str(file)]).split()[0]) - 1
    except:
        rows = 0
    df = pd.read_csv(file, nrows=100)
    mem_per_row = df.memory_usage(deep=True).sum() / 100
    est_mem_mb = (mem_per_row * rows) / (1024**2)
    
    datasets.append({
        'filename': file.name,
        'size_mb': size_mb,
        'rows': rows,
        'est_ram_mb': est_mem_mb,
        'columns': list(df.columns)
    })
data['datasets'] = datasets

print(json.dumps(data, indent=2))
