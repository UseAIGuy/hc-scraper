# Web Dashboard Development Setup Guide

## Prerequisites

### Required Software
- **Node.js**: Version 18.0 or higher
- **Python**: Version 3.9 or higher
- **Git**: Latest version
- **VS Code** (recommended) or your preferred IDE

### Development Tools
- **Node Package Manager**: npm (comes with Node.js) or yarn
- **Python Package Manager**: pip (comes with Python)
- **Database**: Supabase account (existing project)

## Project Structure

```
hc-scraper/
├── dashboard/                 # Web dashboard root
│   ├── frontend/             # React frontend
│   │   ├── src/
│   │   ├── public/
│   │   ├── package.json
│   │   └── vite.config.ts
│   ├── backend/              # FastAPI backend
│   │   ├── app/
│   │   ├── requirements.txt
│   │   └── main.py
│   └── shared/               # Shared types and utilities
├── scraper.py                # Existing scraper
├── config.py                 # Configuration
└── requirements.txt          # Python dependencies
```

## Initial Project Setup

### 1. Create Dashboard Directory Structure

```bash
# From the hc-scraper root directory
mkdir dashboard
cd dashboard
mkdir frontend backend shared
```

### 2. Frontend Setup (React + TypeScript + Vite)

```bash
# Navigate to frontend directory
cd frontend

# Create Vite React TypeScript project
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install

# Install additional dependencies
npm install @types/react @types/react-dom
npm install tailwindcss postcss autoprefixer
npm install react-router-dom @types/react-router-dom
npm install recharts
npm install lucide-react  # For icons
npm install clsx          # For conditional classes
```

### 3. Configure Tailwind CSS

```bash
# Initialize Tailwind CSS
npx tailwindcss init -p
```

Update `tailwind.config.js`:
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563eb',
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
      }
    },
  },
  plugins: [],
}
```

### 4. Backend Setup (FastAPI)

```bash
# Navigate to backend directory
cd ../backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install FastAPI and dependencies
pip install fastapi uvicorn[standard]
pip install sqlalchemy psycopg2-binary
pip install pydantic[email]
pip install python-multipart
pip install websockets
pip install python-jose[cryptography]
pip install passlib[bcrypt]
pip install supabase
pip install asyncpg

# Create requirements.txt
pip freeze > requirements.txt
```

## Environment Configuration

### 1. Frontend Environment Variables

Create `dashboard/frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_APP_NAME=HappyCow Scraper Dashboard
```

### 2. Backend Environment Variables

Create `dashboard/backend/.env`:
```env
# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
DATABASE_URL=postgresql://username:password@host:port/database

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

### 3. Shared Configuration

Create `dashboard/shared/config.py`:
```python
import os
from typing import List
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database
    supabase_url: str
    supabase_key: str
    database_url: str
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## Database Setup

### 1. Extend Supabase Schema

Create `dashboard/backend/database/migrations/001_dashboard_tables.sql`:
```sql
-- Scraping sessions tracking
CREATE TABLE IF NOT EXISTS scraping_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    city_name VARCHAR(100) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'running',
    parameters JSONB,
    restaurants_target INTEGER,
    restaurants_completed INTEGER DEFAULT 0,
    reviews_collected INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Scraping logs for dashboard display
CREATE TABLE IF NOT EXISTS scraping_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES scraping_sessions(id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    level VARCHAR(20) NOT NULL, -- INFO, SUCCESS, WARNING, ERROR
    message TEXT NOT NULL,
    restaurant_url VARCHAR(500),
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User agent rotation tracking
CREATE TABLE IF NOT EXISTS user_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_agent TEXT NOT NULL,
    browser VARCHAR(50),
    os VARCHAR(50),
    device_type VARCHAR(20),
    last_used TIMESTAMP WITH TIME ZONE,
    success_count INTEGER DEFAULT 0,
    blocked_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_scraping_sessions_city ON scraping_sessions(city_name);
CREATE INDEX IF NOT EXISTS idx_scraping_sessions_status ON scraping_sessions(status);
CREATE INDEX IF NOT EXISTS idx_scraping_logs_session ON scraping_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_scraping_logs_timestamp ON scraping_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_agents_active ON user_agents(is_active);
```

### 2. Run Database Migrations

```bash
# Apply migrations to Supabase
# You can run these SQL commands in the Supabase dashboard SQL editor
# Or use the Supabase CLI if you have it installed
```

## Development Workflow

### 1. Start Backend Development Server

```bash
cd dashboard/backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start Frontend Development Server

```bash
cd dashboard/frontend
npm run dev
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## VS Code Configuration

### 1. Recommended Extensions

Create `.vscode/extensions.json`:
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.pylint",
    "ms-python.black-formatter",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode.vscode-json"
  ]
}
```

### 2. Workspace Settings

Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./dashboard/backend/venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "typescript.preferences.importModuleSpecifier": "relative",
  "tailwindCSS.includeLanguages": {
    "typescript": "javascript",
    "typescriptreact": "javascript"
  }
}
```

## Testing Setup

### 1. Frontend Testing

```bash
cd dashboard/frontend
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event
npm install --save-dev vitest jsdom
```

### 2. Backend Testing

```bash
cd dashboard/backend
pip install pytest pytest-asyncio httpx
```

## Git Configuration

### 1. Update .gitignore

Add to existing `.gitignore`:
```
# Dashboard specific
dashboard/frontend/node_modules/
dashboard/frontend/dist/
dashboard/frontend/.env
dashboard/backend/venv/
dashboard/backend/.env
dashboard/backend/__pycache__/
dashboard/backend/*.pyc
dashboard/backend/.pytest_cache/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

### 2. Git Hooks (Optional)

Create `.githooks/pre-commit`:
```bash
#!/bin/sh
# Run frontend linting
cd dashboard/frontend && npm run lint

# Run backend formatting check
cd dashboard/backend && black --check .

# Run tests
cd dashboard/frontend && npm test
cd dashboard/backend && pytest
```

## Common Development Commands

### Frontend Commands
```bash
# Start development server
npm run dev

# Build for production
npm run build

# Run linting
npm run lint

# Run tests
npm test

# Type checking
npm run type-check
```

### Backend Commands
```bash
# Start development server
uvicorn main:app --reload

# Run tests
pytest

# Format code
black .

# Check linting
flake8 .

# Install dependencies
pip install -r requirements.txt
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in environment variables if needed
2. **Database connection**: Verify Supabase credentials are correct
3. **CORS errors**: Ensure frontend URL is in backend CORS settings
4. **Module not found**: Check virtual environment is activated for backend

### Debug Mode

Enable debug logging by setting environment variables:
```bash
# Frontend
VITE_DEBUG=true

# Backend
DEBUG=true
LOG_LEVEL=DEBUG
```

## Next Steps

1. Follow the task breakdown in `.taskmaster/docs/web-dashboard-tasks.md`
2. Start with Task 1: Project Setup and Architecture
3. Set up the basic project structure as outlined above
4. Begin implementing core components according to the PRD

This setup provides a solid foundation for developing the web dashboard with proper tooling, configuration, and development workflow. 