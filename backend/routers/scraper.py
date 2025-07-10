from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any
from database import get_supabase_client
from models import ScrapingRequest, ScrapingSession, ApiResponse, LogEntry
from supabase import Client
import uuid
import asyncio
from datetime import datetime
import sys
import os
from pathlib import Path
import subprocess

# Add the parent directory to the path so we can import the scraper
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the scraper class - handle import errors gracefully
try:
    from scraper import HappyCowScraper
    SCRAPER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import HappyCowScraper: {e}")
    SCRAPER_AVAILABLE = False
    HappyCowScraper = None

from database import SUPABASE_URL, SUPABASE_SERVICE_KEY

router = APIRouter()

# Store active sessions in memory
active_sessions: Dict[str, Dict[str, Any]] = {}

@router.post("/start", response_model=ApiResponse)
async def start_scraping(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks,
    db: Client = Depends(get_supabase_client)
):
    """Start a new scraping session by running the CLI command"""
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Clear any old sessions to avoid confusion
        active_sessions.clear()
        
        # Initialize session
        active_sessions[session_id] = {
            "id": session_id,
            "city_name": request.city_name,
            "max_restaurants": request.max_restaurants,
            "status": "initializing",
            "scraped_restaurants": 0,
            "total_restaurants": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "logs": [],
            "error": None
        }
        
        # Add initial log
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "message": "Scraping session initialized",
            "session_id": session_id
        }
        active_sessions[session_id]["logs"].append(log_entry)
        
        # Start background task
        background_tasks.add_task(run_cli_scraper, session_id, request)
        
        return ApiResponse(
            success=True,
            message="Scraping session started successfully",
            data={"session_id": session_id}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scraping: {str(e)}")

@router.post("/stop/{session_id}", response_model=ApiResponse)
async def stop_scraping(session_id: str):
    """Stop a running scraping session"""
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Update session status
        active_sessions[session_id]["status"] = "stopped"
        active_sessions[session_id]["updated_at"] = datetime.now().isoformat()
        
        return ApiResponse(
            success=True,
            message=f"Stopped scraping session {session_id}",
            data={"session_id": session_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop scraping: {str(e)}")

@router.post("/stop-all", response_model=ApiResponse)
async def stop_all_scraping():
    """Stop all running scraping sessions"""
    try:
        stopped_count = 0
        for session_id in active_sessions:
            if active_sessions[session_id]["status"] in ["active", "starting"]:
                active_sessions[session_id]["status"] = "stopped"
                active_sessions[session_id]["updated_at"] = datetime.now().isoformat()
                stopped_count += 1
        
        return ApiResponse(
            success=True,
            message=f"Stopped {stopped_count} scraping sessions",
            data={"stopped_count": stopped_count}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop all sessions: {str(e)}")

@router.get("/sessions", response_model=List[Dict[str, Any]])
async def get_sessions():
    """Get all scraping sessions"""
    try:
        return list(active_sessions.values())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")

@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a specific scraping session"""
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return active_sessions[session_id]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")

@router.get("/logs", response_model=List[LogEntry])
async def get_logs():
    """Get all logs from all sessions"""
    try:
        all_logs = []
        for session_data in active_sessions.values():
            all_logs.extend(session_data.get("logs", []))
        
        # Sort by timestamp
        all_logs.sort(key=lambda x: x.get("timestamp", datetime.now()))
        
        return all_logs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching logs: {str(e)}")

@router.get("/logs/{session_id}", response_model=List[LogEntry])
async def get_session_logs(session_id: str):
    """Get logs for a specific session"""
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return active_sessions[session_id].get("logs", [])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching logs: {str(e)}")

async def run_cli_scraper(session_id: str, request: ScrapingRequest):
    """Background task to run the CLI scraper"""
    try:
        # Update session status
        active_sessions[session_id]["status"] = "active"
        active_sessions[session_id]["updated_at"] = datetime.now().isoformat()
        
        # Build CLI command
        cli_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "cli.py")
        
        cmd = [
            sys.executable, cli_path,
            "--cities", request.city_name,
            "--max-restaurants", str(request.max_restaurants),
            "--workers", "1",  # Single worker for web interface
            "--anti-captcha",  # Use anti-captcha mode
            "--delay-min", "10.0",  # Conservative delays
            "--delay-max", "25.0"
        ]
        
        # Add log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "message": f"Starting CLI scraper for {request.city_name}",
            "session_id": session_id
        }
        active_sessions[session_id]["logs"].append(log_entry)
        
        print(f"[DEBUG] Running command: {' '.join(cmd)}")
        
        # Use synchronous subprocess to avoid Windows asyncio issues
        import subprocess
        
        # Set environment variables to fix Windows Unicode issues
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUNBUFFERED'] = '1'  # Force unbuffered output
        
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(cli_path),
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout
            env=env,
            encoding='utf-8',
            errors='replace'  # Replace problematic characters instead of crashing
        )
        
        print(f"[DEBUG] CLI stdout: {result.stdout}")
        print(f"[DEBUG] CLI stderr: {result.stderr}")
        print(f"[DEBUG] CLI return code: {result.returncode}")
        
        # Process stdout
        if result.stdout:
            for line in result.stdout.split('\n'):
                if line.strip():
                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "level": "INFO",
                        "message": line.strip(),
                        "session_id": session_id
                    }
                    active_sessions[session_id]["logs"].append(log_entry)
        
        # Process stderr
        if result.stderr:
            for line in result.stderr.split('\n'):
                if line.strip():
                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "level": "ERROR",
                        "message": line.strip(),
                        "session_id": session_id
                    }
                    active_sessions[session_id]["logs"].append(log_entry)
        
        # Update final status
        if result.returncode == 0:
            active_sessions[session_id]["status"] = "completed"
            final_message = "Scraping completed successfully"
        else:
            active_sessions[session_id]["status"] = "failed"
            final_message = f"Scraping failed with exit code {result.returncode}"
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO" if result.returncode == 0 else "ERROR",
            "message": final_message,
            "session_id": session_id
        }
        active_sessions[session_id]["logs"].append(log_entry)
        active_sessions[session_id]["updated_at"] = datetime.now().isoformat()
        
        print(f"[DEBUG] CLI completed with return code: {result.returncode}")
        
    except Exception as e:
        print(f"[DEBUG] Exception in run_cli_scraper: {str(e)}")
        import traceback
        print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
        
        # Update session with error
        active_sessions[session_id]["status"] = "failed"
        active_sessions[session_id]["error"] = str(e)
        active_sessions[session_id]["updated_at"] = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "ERROR",
            "message": f"CLI scraper failed: {str(e)}",
            "session_id": session_id
        }
        active_sessions[session_id]["logs"].append(log_entry) 