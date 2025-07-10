from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ScrapingStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"

class CityStatus(BaseModel):
    city_name: str
    total_restaurants: int
    scraped_restaurants: int
    completion_percentage: float
    status: ScrapingStatus
    last_updated: Optional[datetime] = None
    error_message: Optional[str] = None

class ScrapingRequest(BaseModel):
    city_name: str = Field(..., description="Name of the city to scrape")
    max_restaurants: int = Field(50, ge=1, le=1000, description="Maximum number of restaurants to scrape")
    concurrent_sessions: int = Field(3, ge=1, le=10, description="Number of concurrent scraping sessions")
    include_reviews: bool = Field(True, description="Whether to scrape reviews")
    delay_between_requests: float = Field(2.0, ge=0.5, le=10.0, description="Delay between requests in seconds")

class ScrapingSession(BaseModel):
    session_id: str
    city_name: str
    status: ScrapingStatus
    parameters: ScrapingRequest
    created_at: datetime
    updated_at: datetime
    restaurants_scraped: int = 0
    total_restaurants: int = 0
    error_message: Optional[str] = None

class RestaurantSummary(BaseModel):
    id: str
    name: str
    city_name: str
    rating: Optional[float] = None
    review_count: Optional[int] = None
    has_details: bool = False
    has_reviews: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

class DashboardStats(BaseModel):
    total_cities: int
    total_restaurants: int
    active_sessions: int
    completed_sessions: int
    total_reviews: int
    last_activity: Optional[datetime] = None

class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str
    session_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class UserAgentStats(BaseModel):
    user_agent: str
    browser: str
    os: str
    success_rate: float
    total_requests: int
    last_used: Optional[datetime] = None
    is_active: bool = True

# Response models
class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

class PaginatedResponse(BaseModel):
    success: bool
    data: List[Any]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool 