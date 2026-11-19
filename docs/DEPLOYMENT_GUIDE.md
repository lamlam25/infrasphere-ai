# InfraSphere AI — Real-World Production & Deployment Blueprint

This guide details the step-by-step process for transitioning InfraSphere AI from the local development/hackathon environment into a live, real-world operational platform.

---

## 1. Transitioning to Real-World Intelligence & APIs

Currently, the system is in offline/demo mode (`LLM_PROVIDER=mock`, `ENABLE_DEMO_DATA=true`). To activate real-world AI reasoning and live telemetry:

### 1.1 Connect a Real LLM Provider
In your `.env` file, switch `LLM_PROVIDER` to one of the following:

#### Option A: OpenAI (GPT-4o / GPT-4o-mini)
```bash
LLM_PROVIDER=openai
LLM_API_KEY=sk-proj-your-openai-api-key
LLM_MODEL=gpt-4o
```

#### Option B: Google Gemini (via OpenAI-compatible endpoint)
```bash
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_API_KEY=your-gemini-api-key
LLM_MODEL=gemini-1.5-flash
```

#### Option C: Local Self-Hosted LLM (Data Sovereignty for Bangladesh Government)
To keep all sensitive national infrastructure telemetry strictly within Bangladesh borders:
```bash
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=http://localhost:11434/v1    # Ollama or vLLM endpoint
LLM_MODEL=llama3.1:8b                     # Or mistral / bangla-mistral
```

---

### 1.2 Enable Real Multilingual Embeddings (English & Bengali)
Switch from mock embeddings to real dense vector embeddings:
```bash
EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=BAAI/bge-m3               # Or istiaqfuad/triBne-e5-small for Bengali
```
When this is set, uploaded PDFs and documents are transformed into high-dimensional semantic vectors and indexed into Qdrant.

---

### 1.3 Connect Live Bangladesh Telemetry
```bash
# Disable synthetic mock data
ENABLE_DEMO_DATA=false
ENABLE_SYNTHETIC_INCIDENTS=false

# Enable live FFWC telemetry
FFWC_ENABLED=true
FFWC_API_BASE_URL=https://api.ffwc.gov.bd/v1    # Or BWDB API endpoint
FFWC_API_KEY=your_registered_ffwc_api_token

# Enable OpenStreetMap real roads query
OSM_ENABLED=true
```

---

## 2. Production Database & Storage Migration

### 2.1 Migrate from SQLite to Managed PostgreSQL
1. Provision a PostgreSQL instance (e.g. AWS RDS, Google Cloud SQL, Supabase, or Railway).
2. Install `asyncpg` in backend:
   ```bash
   pip install asyncpg
   ```
3. Update `DATABASE_URL` in `.env`:
   ```bash
   DATABASE_URL=postgresql+asyncpg://db_user:db_password@db_host:5432/infrasphere
   ```

### 2.2 Migrate from Local Qdrant to Qdrant Cloud
1. Create a free cluster at [cloud.qdrant.io](https://cloud.qdrant.io/).
2. Set Qdrant URL and API key in backend config:
   ```bash
   QDRANT_URL=https://your-cluster-id.qdrant.tech:6333
   QDRANT_API_KEY=your-qdrant-cloud-api-key
   ```

---

## 3. Deployment Options

### 🚀 Path A: 10-Minute Cloud Deployment (Railway / Render)
Recommended for live investor demos and public hackathon URLs.

1. **Deploy Backend + PostgreSQL on Railway:**
   - Push your repo to GitHub:
     ```bash
     git add .
     git commit -m "Deploy InfraSphere AI"
     git push origin main
     ```
   - Open [Railway.app](https://railway.app), click **New Project** → **Deploy from GitHub repo**.
   - Select the `infrasphere-ai` repo, set root directory to `backend`.
   - Add a PostgreSQL database service with 1 click.
   - Add environment variables (`JWT_SECRET`, `LLM_API_KEY`, etc.).
   - Railway will detect the `Dockerfile` and deploy the API with a public HTTPS URL (e.g. `https://infrasphere-backend.up.railway.app`).

2. **Deploy Frontend on Vercel:**
   - Go to [Vercel.com](https://vercel.com) → **Add New Project**.
   - Select the `infrasphere-ai/frontend` directory.
   - Set Environment Variable:
     ```bash
     VITE_API_BASE_URL=https://infrasphere-backend.up.railway.app
     ```
   - Click **Deploy**. Your command center is now live on a global CDN!

---

### 🏢 Path B: Google Cloud Platform (Enterprise Deployment)
- **Container Registry:** Push Docker image to Google Artifact Registry.
- **Backend:** Deploy to **Google Cloud Run** (auto-scaling 0 to N instances, serverless, HTTPS termination included).
- **Database:** **Google Cloud SQL for PostgreSQL 16**.
- **Vector Search:** Qdrant Cloud or Vertex AI Vector Search.
- **Frontend:** **Firebase Hosting** or Cloud Storage + Cloud CDN.

---

### 🛡️ Path C: Bangladesh National Data Center / On-Premises
For deployment within government networks (e.g., Bangladesh Computer Council - BCC / RHD data centers):
1. Use the pre-configured `docker-compose.yml`:
   ```bash
   docker compose up -d --build
   ```
2. Configure Nginx reverse proxy with SSL certificates (`certbot` / Let's Encrypt or government PKI):
   ```nginx
   server {
       listen 443 ssl http2;
       server_name infraops.gov.bd;

       ssl_certificate /etc/ssl/certs/infraops.crt;
       ssl_certificate_key /etc/ssl/private/infraops.key;

       location / {
           proxy_pass http://localhost:5173;
       }

       location /api/ {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
