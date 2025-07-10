from fastapi import APIRouter, HTTPException, Depends
from typing import List
from database import get_supabase_client
from models import DashboardStats, CityStatus, ScrapingStatus, ApiResponse
from supabase import Client

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: Client = Depends(get_supabase_client)):
    """Get overall dashboard statistics"""
    try:
        # Get total restaurants
        restaurants_response = db.table("restaurants").select("*", count="exact").execute()
        total_restaurants = restaurants_response.count if restaurants_response.count else 0
        
        # Get total reviews
        reviews_response = db.table("reviews").select("*", count="exact").execute()
        total_reviews = reviews_response.count if reviews_response.count else 0
        
        # Get unique cities
        cities_response = db.table("restaurants").select("city_name").execute()
        unique_cities = set()
        if cities_response.data:
            unique_cities = {r["city_name"] for r in cities_response.data if r["city_name"]}
        
        # For now, we'll simulate sessions data since we don't have a sessions table yet
        active_sessions = 0
        completed_sessions = 0
        
        return DashboardStats(
            total_cities=len(unique_cities),
            total_restaurants=total_restaurants,
            active_sessions=active_sessions,
            completed_sessions=completed_sessions,
            total_reviews=total_reviews,
            last_activity=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")

@router.get("/cities", response_model=List[CityStatus])
async def get_cities_status(db: Client = Depends(get_supabase_client)):
    """Get status of all cities"""
    try:
        # Get restaurant counts by city
        restaurants_response = db.table("restaurants").select("city_name, rating, phone, website").execute()
        
        if not restaurants_response.data:
            return []
        
        # Group by city and calculate stats
        city_stats = {}
        for restaurant in restaurants_response.data:
            city_name = restaurant.get("city_name", "Unknown")
            if city_name not in city_stats:
                city_stats[city_name] = {
                    "total": 0,
                    "with_details": 0
                }
            
            city_stats[city_name]["total"] += 1
            
            # Check if restaurant has detailed data
            if restaurant.get("rating") or restaurant.get("phone") or restaurant.get("website"):
                city_stats[city_name]["with_details"] += 1
        
        # Convert to CityStatus objects
        cities = []
        for city_name, stats in city_stats.items():
            total = stats["total"]
            scraped = stats["with_details"]
            completion = (scraped / total * 100) if total > 0 else 0
            
            # Determine status based on completion
            if completion == 100:
                status = ScrapingStatus.COMPLETED
            elif completion > 0:
                status = ScrapingStatus.ACTIVE
            else:
                status = ScrapingStatus.PENDING
            
            cities.append(CityStatus(
                city_name=city_name,
                total_restaurants=total,
                scraped_restaurants=scraped,
                completion_percentage=round(completion, 1),
                status=status
            ))
        
        return sorted(cities, key=lambda x: x.city_name)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cities status: {str(e)}")

@router.get("/cities/{city_name}", response_model=CityStatus)
async def get_city_status(city_name: str, db: Client = Depends(get_supabase_client)):
    """Get status of a specific city"""
    try:
        # Get restaurants for this city
        restaurants_response = db.table("restaurants").select("*").eq("city_name", city_name).execute()
        
        if not restaurants_response.data:
            raise HTTPException(status_code=404, detail=f"City '{city_name}' not found")
        
        total = len(restaurants_response.data)
        with_details = sum(1 for r in restaurants_response.data 
                          if r.get("rating") or r.get("phone") or r.get("website"))
        
        completion = (with_details / total * 100) if total > 0 else 0
        
        # Determine status
        if completion == 100:
            status = ScrapingStatus.COMPLETED
        elif completion > 0:
            status = ScrapingStatus.ACTIVE
        else:
            status = ScrapingStatus.PENDING
        
        return CityStatus(
            city_name=city_name,
            total_restaurants=total,
            scraped_restaurants=with_details,
            completion_percentage=round(completion, 1),
            status=status
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching city status: {str(e)}") 