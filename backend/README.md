# VeganVoyage Backend API

## Environment Configuration

The backend uses the **service role key** for Supabase operations, which provides full admin access to the database. This is different from the frontend, which uses the **anon key**.

### Required Environment Variables

Create a `.env` file in the `backend/` directory with:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_SERVICE_KEY=your_supabase_service_role_key_here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Key Differences from Frontend

| Component | Key Type | Purpose |
|-----------|----------|---------|
| **Backend API** | Service Role Key | Full admin access, bypasses RLS |
| **Frontend** | Anon Key | Limited access, enforces RLS policies |

### Why Service Role Key?

1. **Full Database Access**: Backend operations often need to read/write data across all tables
2. **Bypasses RLS**: Server-side operations don't need row-level security restrictions
3. **Admin Operations**: Can perform maintenance, bulk operations, and system-level tasks

### Security Note

⚠️ **Never expose the service role key to the client side!** It should only be used in server environments.

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Running the API

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` 