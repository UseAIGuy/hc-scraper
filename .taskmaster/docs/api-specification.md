# Web Dashboard API Specification

## Base Configuration

- **Base URL**: `http://localhost:8000` (development)
- **API Prefix**: `/api/v1`
- **Content Type**: `application/json`
- **Authentication**: JWT Bearer tokens

## Authentication

### POST /api/v1/auth/login
**Description**: Authenticate user and receive JWT token

**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Response** (200):
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### POST /api/v1/auth/refresh
**Description**: Refresh JWT token

**Headers**: `Authorization: Bearer <token>`

**Response** (200):
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 1800
}
```

## City Management

### GET /api/v1/cities/status
**Description**: Get status overview for all cities

**Response** (200):
```json
{
  "cities": [
    {
      "name": "Austin",
      "country": "USA",
      "path": "north_america/usa/texas/austin",
      "total_restaurants": 200,
      "scraped_restaurants": 152,
      "completion_percentage": 76.0,
      "total_reviews": 1240,
      "last_scraped": "2024-01-15T10:30:00Z",
      "status": "completed|in_progress|paused|error|not_started",
      "current_session_id": "uuid|null"
    }
  ],
  "summary": {
    "total_cities": 10,
    "total_restaurants": 2500,
    "total_scraped": 1800,
    "total_reviews": 15000,
    "cities_completed": 6,
    "cities_in_progress": 2,
    "overall_completion": 72.0
  }
}
```

### GET /api/v1/cities/{city_name}/details
**Description**: Get detailed information for a specific city

**Path Parameters**:
- `city_name`: String - Name of the city

**Response** (200):
```json
{
  "city": {
    "name": "Austin",
    "country": "USA",
    "path": "north_america/usa/texas/austin",
    "total_restaurants": 200,
    "scraped_restaurants": 152,
    "completion_percentage": 76.0,
    "total_reviews": 1240,
    "last_scraped": "2024-01-15T10:30:00Z",
    "status": "completed",
    "estimated_time_remaining": "00:45:00"
  },
  "recent_sessions": [
    {
      "id": "uuid",
      "started_at": "2024-01-15T09:00:00Z",
      "ended_at": "2024-01-15T10:30:00Z",
      "status": "completed",
      "restaurants_scraped": 25,
      "reviews_collected": 180,
      "success_rate": 96.0,
      "error_count": 1
    }
  ],
  "statistics": {
    "avg_reviews_per_restaurant": 8.2,
    "avg_scraping_time": "00:02:30",
    "success_rate": 94.5,
    "common_errors": [
      {
        "error_type": "timeout",
        "count": 5,
        "percentage": 2.5
      }
    ]
  }
}
```

### GET /api/v1/cities/{city_name}/restaurants
**Description**: Get restaurants for a specific city with pagination

**Path Parameters**:
- `city_name`: String - Name of the city

**Query Parameters**:
- `page`: Integer - Page number (default: 1)
- `limit`: Integer - Items per page (default: 50, max: 100)
- `status`: String - Filter by scraping status (scraped|not_scraped|error)

**Response** (200):
```json
{
  "restaurants": [
    {
      "id": "uuid",
      "name": "Green Seed Vegan",
      "url": "https://www.happycow.net/reviews/green-seed-vegan-austin-12345",
      "scraped": true,
      "scraped_at": "2024-01-15T10:15:00Z",
      "rating": 4.5,
      "review_count": 23,
      "address": "123 Main St, Austin, TX",
      "phone": "+1-512-555-0123",
      "website": "https://greenseedvegan.com",
      "data_quality": {
        "completeness": 85.0,
        "missing_fields": ["hours", "social_media"]
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 200,
    "pages": 4,
    "has_next": true,
    "has_prev": false
  }
}
```

## Scraper Control

### POST /api/v1/scrape/start
**Description**: Start a new scraping session

**Request Body**:
```json
{
  "city_name": "Austin",
  "max_restaurants": 50,
  "concurrent_sessions": 3,
  "delay_settings": {
    "min_delay": 3.0,
    "max_delay": 6.0,
    "type": "normal"
  },
  "user_agent_settings": {
    "rotation_mode": "per_request",
    "browser_mix": {
      "chrome": 60,
      "firefox": 25,
      "safari": 10,
      "edge": 5
    },
    "os_mix": {
      "windows": 70,
      "macos": 20,
      "linux": 10
    },
    "randomization_level": "moderate"
  },
  "resume_mode": true
}
```

**Response** (201):
```json
{
  "session_id": "uuid",
  "status": "starting",
  "estimated_duration": "01:30:00",
  "estimated_completion": "2024-01-15T12:00:00Z",
  "message": "Scraping session started successfully"
}
```

### POST /api/v1/scrape/pause
**Description**: Pause current scraping session

**Request Body**:
```json
{
  "session_id": "uuid"
}
```

**Response** (200):
```json
{
  "session_id": "uuid",
  "status": "paused",
  "message": "Scraping session paused"
}
```

### POST /api/v1/scrape/stop
**Description**: Stop current scraping session

**Request Body**:
```json
{
  "session_id": "uuid"
}
```

**Response** (200):
```json
{
  "session_id": "uuid",
  "status": "stopped",
  "message": "Scraping session stopped"
}
```

### GET /api/v1/scrape/status
**Description**: Get current scraping status

**Response** (200):
```json
{
  "active_sessions": [
    {
      "id": "uuid",
      "city_name": "Austin",
      "status": "running",
      "started_at": "2024-01-15T10:00:00Z",
      "progress": {
        "restaurants_target": 50,
        "restaurants_completed": 25,
        "percentage": 50.0,
        "reviews_collected": 180,
        "current_restaurant": "Green Seed Vegan",
        "estimated_remaining": "00:30:00"
      },
      "statistics": {
        "success_rate": 96.0,
        "avg_time_per_restaurant": "00:01:20",
        "error_count": 2
      }
    }
  ],
  "queue": [
    {
      "city_name": "Portland",
      "position": 1,
      "estimated_start": "2024-01-15T12:30:00Z"
    }
  ]
}
```

## Session Management

### GET /api/v1/sessions
**Description**: Get scraping sessions with pagination

**Query Parameters**:
- `page`: Integer - Page number (default: 1)
- `limit`: Integer - Items per page (default: 20)
- `status`: String - Filter by status
- `city`: String - Filter by city

**Response** (200):
```json
{
  "sessions": [
    {
      "id": "uuid",
      "city_name": "Austin",
      "started_at": "2024-01-15T09:00:00Z",
      "ended_at": "2024-01-15T10:30:00Z",
      "status": "completed",
      "parameters": {
        "max_restaurants": 50,
        "concurrent_sessions": 3
      },
      "results": {
        "restaurants_target": 50,
        "restaurants_completed": 48,
        "reviews_collected": 340,
        "success_rate": 96.0,
        "error_count": 2
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

### GET /api/v1/sessions/{session_id}
**Description**: Get detailed session information

**Path Parameters**:
- `session_id`: UUID - Session identifier

**Response** (200):
```json
{
  "session": {
    "id": "uuid",
    "city_name": "Austin",
    "started_at": "2024-01-15T09:00:00Z",
    "ended_at": "2024-01-15T10:30:00Z",
    "status": "completed",
    "parameters": {
      "max_restaurants": 50,
      "concurrent_sessions": 3,
      "delay_settings": {
        "min_delay": 3.0,
        "max_delay": 6.0
      }
    },
    "results": {
      "restaurants_target": 50,
      "restaurants_completed": 48,
      "reviews_collected": 340,
      "success_rate": 96.0,
      "error_count": 2,
      "duration": "01:30:00"
    }
  },
  "logs": [
    {
      "timestamp": "2024-01-15T09:00:00Z",
      "level": "INFO",
      "message": "Starting scraping session for Austin",
      "details": {}
    }
  ]
}
```

## User Agent Management

### GET /api/v1/user-agents
**Description**: Get user agents with performance statistics

**Query Parameters**:
- `active_only`: Boolean - Show only active user agents
- `browser`: String - Filter by browser type

**Response** (200):
```json
{
  "user_agents": [
    {
      "id": "uuid",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
      "browser": "Chrome",
      "os": "Windows",
      "device_type": "Desktop",
      "success_count": 150,
      "blocked_count": 2,
      "success_rate": 98.7,
      "last_used": "2024-01-15T10:00:00Z",
      "is_active": true
    }
  ]
}
```

### POST /api/v1/user-agents
**Description**: Add custom user agent

**Request Body**:
```json
{
  "user_agent": "Mozilla/5.0 (Custom Browser)...",
  "browser": "Custom",
  "os": "Linux",
  "device_type": "Desktop"
}
```

### PUT /api/v1/user-agents/{user_agent_id}/status
**Description**: Update user agent status

**Request Body**:
```json
{
  "is_active": false
}
```

## Data Export

### GET /api/v1/export/restaurants
**Description**: Export restaurant data

**Query Parameters**:
- `format`: String - Export format (csv|json)
- `city`: String - Filter by city
- `scraped_only`: Boolean - Export only scraped restaurants

**Response** (200):
- Content-Type: `application/json` or `text/csv`
- Content-Disposition: `attachment; filename="restaurants.csv"`

### GET /api/v1/export/reviews
**Description**: Export review data

**Query Parameters**:
- `format`: String - Export format (csv|json)
- `city`: String - Filter by city
- `date_from`: String - ISO date filter
- `date_to`: String - ISO date filter

### GET /api/v1/export/logs
**Description**: Export scraping logs

**Query Parameters**:
- `format`: String - Export format (csv|json)
- `session_id`: UUID - Filter by session
- `level`: String - Filter by log level

## Analytics

### GET /api/v1/analytics/overview
**Description**: Get analytics overview

**Query Parameters**:
- `period`: String - Time period (day|week|month|year)

**Response** (200):
```json
{
  "period": "week",
  "metrics": {
    "restaurants_scraped": 450,
    "reviews_collected": 3200,
    "sessions_completed": 15,
    "avg_success_rate": 94.5,
    "total_scraping_time": "25:30:00"
  },
  "trends": {
    "restaurants_per_day": [45, 52, 38, 61, 49, 55, 50],
    "success_rate_trend": [95.2, 94.8, 93.1, 96.0, 94.5, 95.8, 94.2]
  }
}
```

### GET /api/v1/analytics/performance
**Description**: Get performance analytics

**Response** (200):
```json
{
  "performance": {
    "avg_time_per_restaurant": "00:02:15",
    "avg_reviews_per_restaurant": 7.1,
    "fastest_city": "Portland",
    "slowest_city": "New York",
    "peak_performance_hour": 14,
    "efficiency_by_hour": [
      {"hour": 0, "avg_time": "00:02:45"},
      {"hour": 1, "avg_time": "00:02:30"}
    ]
  }
}
```

## WebSocket Events

### Connection
**URL**: `ws://localhost:8000/api/v1/ws`
**Authentication**: Query parameter `token=<jwt_token>`

### Event Types

#### 1. Log Messages
```json
{
  "type": "log",
  "data": {
    "session_id": "uuid",
    "timestamp": "2024-01-15T10:00:00Z",
    "level": "INFO|SUCCESS|WARNING|ERROR",
    "message": "Starting restaurant scraping: Green Seed Vegan",
    "restaurant_url": "https://www.happycow.net/...",
    "details": {}
  }
}
```

#### 2. Progress Updates
```json
{
  "type": "progress",
  "data": {
    "session_id": "uuid",
    "city_name": "Austin",
    "restaurants_completed": 25,
    "restaurants_target": 50,
    "percentage": 50.0,
    "reviews_collected": 180,
    "current_restaurant": "Green Seed Vegan",
    "estimated_remaining": "00:30:00"
  }
}
```

#### 3. Status Changes
```json
{
  "type": "status",
  "data": {
    "session_id": "uuid",
    "old_status": "running",
    "new_status": "paused",
    "timestamp": "2024-01-15T10:00:00Z",
    "message": "Session paused by user"
  }
}
```

#### 4. Error Notifications
```json
{
  "type": "error",
  "data": {
    "session_id": "uuid",
    "error_type": "timeout|blocked|network|parsing",
    "restaurant_url": "https://www.happycow.net/...",
    "message": "Request timeout after 30 seconds",
    "timestamp": "2024-01-15T10:00:00Z",
    "retry_count": 2
  }
}
```

#### 5. Statistics Updates
```json
{
  "type": "statistics",
  "data": {
    "session_id": "uuid",
    "success_rate": 96.0,
    "avg_time_per_restaurant": "00:01:20",
    "error_count": 2,
    "reviews_per_minute": 12.5
  }
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "max_restaurants",
      "reason": "Value must be between 1 and 500"
    },
    "timestamp": "2024-01-15T10:00:00Z"
  }
}
```

### Common Error Codes
- `VALIDATION_ERROR` (400): Invalid request parameters
- `UNAUTHORIZED` (401): Missing or invalid authentication
- `FORBIDDEN` (403): Insufficient permissions
- `NOT_FOUND` (404): Resource not found
- `CONFLICT` (409): Resource conflict (e.g., session already running)
- `RATE_LIMITED` (429): Too many requests
- `INTERNAL_ERROR` (500): Server error

## Rate Limiting

- **Authentication endpoints**: 5 requests per minute
- **Scraper control endpoints**: 10 requests per minute
- **Data retrieval endpoints**: 100 requests per minute
- **Export endpoints**: 5 requests per hour

Headers included in responses:
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Requests remaining in window
- `X-RateLimit-Reset`: Time when rate limit resets

This API specification provides a comprehensive foundation for building the web dashboard backend with clear contracts for all functionality. 