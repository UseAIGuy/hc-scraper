from fastapi import APIRouter, HTTPException, Depends
from typing import List
from database import get_supabase_client
from models import RestaurantSummary, PaginatedResponse
from supabase import Client

router = APIRouter()

@router.get("/", response_model=List[str])
async def get_cities(db: Client = Depends(get_supabase_client)):
    """Get list of all cities from city_queue"""
    try:
        response = db.table("city_queue").select("city, state").execute()
        
        if not response.data:
            return []
        
        # Format cities as "City, State" for better UX
        cities = []
        for item in response.data:
            city_name = item.get("city", "")
            state_name = item.get("state", "")
            if city_name:
                if state_name:
                    cities.append(f"{city_name}, {state_name}")
                else:
                    cities.append(city_name)
        
        return sorted(list(set(cities)))  # Remove duplicates and sort
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cities: {str(e)}")

@router.get("/{city_name}/restaurants", response_model=PaginatedResponse)
async def get_city_restaurants(
    city_name: str,
    page: int = 1,
    per_page: int = 20,
    db: Client = Depends(get_supabase_client)
):
    """Get restaurants for a specific city with pagination"""
    try:
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get total count
        count_response = db.table("restaurants").select("*", count="exact").eq("city_name", city_name).execute()
        total = count_response.count if count_response.count else 0
        
        if total == 0:
            return PaginatedResponse(
                success=True,
                data=[],
                total=0,
                page=page,
                per_page=per_page,
                has_next=False,
                has_prev=False
            )
        
        # Get restaurants with pagination
        restaurants_response = db.table("restaurants").select("*").eq("city_name", city_name).range(offset, offset + per_page - 1).execute()
        
        restaurants = []
        for r in restaurants_response.data:
            restaurants.append(RestaurantSummary(
                id=r["id"],
                name=r["name"],
                city_name=r["city_name"],
                rating=r.get("rating"),
                review_count=r.get("review_count"),
                has_details=bool(r.get("phone") or r.get("website") or r.get("rating")),
                has_reviews=False,  # TODO: Check reviews table
                created_at=r["created_at"],
                updated_at=r.get("updated_at")
            ))
        
        return PaginatedResponse(
            success=True,
            data=restaurants,
            total=total,
            page=page,
            per_page=per_page,
            has_next=offset + per_page < total,
            has_prev=page > 1
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching restaurants: {str(e)}")

@router.get("/{city_name}/stats")
async def get_city_detailed_stats(city_name: str, db: Client = Depends(get_supabase_client)):
    """Get detailed statistics for a city"""
    try:
        # Get all restaurants for this city
        restaurants_response = db.table("restaurants").select("*").eq("city_name", city_name).execute()
        
        if not restaurants_response.data:
            raise HTTPException(status_code=404, detail=f"City '{city_name}' not found")
        
        restaurants = restaurants_response.data
        total_restaurants = len(restaurants)
        
        # Count restaurants with various data
        with_rating = sum(1 for r in restaurants if r.get("rating"))
        with_phone = sum(1 for r in restaurants if r.get("phone"))
        with_website = sum(1 for r in restaurants if r.get("website"))
        with_address = sum(1 for r in restaurants if r.get("address"))
        with_details = sum(1 for r in restaurants if r.get("rating") or r.get("phone") or r.get("website"))
        
        # Calculate average rating
        ratings = [r["rating"] for r in restaurants if r.get("rating")]
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        
        return {
            "city_name": city_name,
            "total_restaurants": total_restaurants,
            "with_details": with_details,
            "with_rating": with_rating,
            "with_phone": with_phone,
            "with_website": with_website,
            "with_address": with_address,
            "average_rating": round(avg_rating, 2) if avg_rating else None,
            "completion_percentage": round((with_details / total_restaurants * 100), 1) if total_restaurants > 0 else 0
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching city stats: {str(e)}") 