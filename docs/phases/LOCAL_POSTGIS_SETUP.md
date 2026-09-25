# LOCAL POSTGIS SETUP
**Project:** SIH 26059

## Prerequisites
- macOS/Linux environment
- `sudo` privileges to install Homebrew and system packages

## Setup Instructions

**1. Install Homebrew**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**2. Install PostgreSQL and PostGIS**
```bash
brew install postgresql postgis
```

**3. Start PostgreSQL Service**
```bash
brew services start postgresql
```

**4. Create Database and Enable PostGIS**
```bash
createdb sih_26059_db
psql -d sih_26059_db -c "CREATE EXTENSION postgis;"
```

**5. Initialize Schema and Seed Data**
```bash
python scripts/database/init_db.py
python scripts/database/seed_vessels_and_ports.py
```

## Shutdown
```bash
brew services stop postgresql
```
