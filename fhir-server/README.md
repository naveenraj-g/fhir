# ⚙️ Environment Configuration

This project uses **Pydantic Settings** to load environment variables.

## 1️⃣ Create `.env` file

Copy:

```bash
cp .env.example .env
```

# 🧪 Running Locally (Without Docker)

## Install uv (if not installed)

```bash
pip install uv
```

## Install dependencies

```bash
uv sync
```

## Run development server

```bash
uv run fastapi dev app/main.py
```

### Open in browser:

```bash
http://localhost:8000/docs
```

# 🐳 Running with Docker (Local or VPS)

## Build & Run

```bash
docker compose up --build
```

## Run in background

```bash
docker compose up -d --build
```

## Stop containers

```bash
docker compose down
```

# 🔐 Environment Variables in Docker

- .env is NOT copied into Docker image
- Docker injects variables at runtime using:

```bash
env_file:
  - .env
```

- Pydantic reads from system environment automatically

#### This ensures:

- Secrets are not baked into image
- Safe for GitHub
- Safe for VPS deployment

---

# 🚀 Production Deployment (VPS)

## On VPS

### 1️⃣ Install Docker

```bash
sudo apt update
sudo apt install docker.io docker-compose-plugin -y

```

### 2️⃣ Clone project

```bash
git clone <your-repo-url>
cd server
```

### 3️⃣ Create .env

```bash
cp .env.example .env
```

### 4️⃣ Run in background

```bash
docker compose up -d --build
```

#### Your API will run on:

```bash
http://your-vps-ip:8000/docs
```

# 📦 Dependency Management (uv)

## Add package

```bash
uv add package_name
```

## Remove package

```bash
uv remove package_name
```

## Sync dependencies

```bash
uv sync
```
