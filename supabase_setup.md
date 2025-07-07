-- ================================
-- SUPABASE DATABASE SETUP
-- ================================
-- Run this SQL in your Supabase SQL Editor to create the restaurants table

-- Create restaurants table
CREATE TABLE IF NOT EXISTS restaurants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Basic Info
    name TEXT NOT NULL,
    description TEXT,
    cuisine_types TEXT[], -- Array of cuisine types
    vegan_status TEXT CHECK (vegan_status IN ('fully vegan', 'vegan options', 'vegan-friendly', 'vegetarian')),
    
    -- Location
    address TEXT,
    city TEXT NOT NULL,
    state TEXT,
    country TEXT DEFAULT 'USA',
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Contact Info
    phone TEXT,
    website TEXT,
    instagram TEXT,
    facebook TEXT,
    
    -- Business Details
    hours JSONB, -- Store hours as JSON object
    price_range TEXT,
    features TEXT[], -- Array of features like 'delivery', 'outdoor seating'
    
    -- Reviews & Ratings
    rating DECIMAL(2,1) CHECK (rating >= 0 AND rating <= 5),
    review_count INTEGER DEFAULT 0,
    recent_reviews JSONB, -- Store recent reviews as JSON array
    
    -- Meta & Source
    happycow_url TEXT UNIQUE NOT NULL, -- Unique constraint for deduplication
    happycow_id TEXT,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Search optimization
    search_vector TSVECTOR
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_restaurants_city ON restaurants(city);
CREATE INDEX IF NOT EXISTS idx_restaurants_vegan_status ON restaurants(vegan_status);
CREATE INDEX IF NOT EXISTS idx_restaurants_rating ON restaurants(rating);
CREATE INDEX IF NOT EXISTS idx_restaurants_location ON restaurants USING GIST(
    ll_to_earth(latitude, longitude)
) WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_restaurants_happycow_id ON restaurants(happycow_id);
CREATE INDEX IF NOT EXISTS idx_restaurants_search ON restaurants USING GIN(search_vector);

-- Create a function to update the search vector
CREATE OR REPLACE FUNCTION update_restaurants_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.cuisine_types, ' '), '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.city, '')), 'D');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update search vector
CREATE TRIGGER restaurants_search_vector_update
    BEFORE INSERT OR UPDATE ON restaurants
    FOR EACH ROW
    EXECUTE FUNCTION update_restaurants_search_vector();

-- Create a view for easy querying with distance calculations
CREATE OR REPLACE VIEW restaurants_with_distance AS
SELECT 
    r.*,
    -- Add helper fields for the application
    CASE 
        WHEN rating >= 4.5 THEN 'excellent'
        WHEN rating >= 4.0 THEN 'very good'
        WHEN rating >= 3.5 THEN 'good'
        WHEN rating >= 3.0 THEN 'average'
        ELSE 'below average'
    END as rating_category,
    
    CASE 
        WHEN array_length(features, 1) > 0 THEN features
        ELSE ARRAY[]::TEXT[]
    END as feature_list
FROM restaurants r;

-- Create RLS (Row Level Security) policies if needed
-- ALTER TABLE restaurants ENABLE ROW LEVEL SECURITY;

-- Sample queries for testing and API development

-- 1. Find all restaurants in a city
-- SELECT * FROM restaurants WHERE city = 'Austin' ORDER BY rating DESC;

-- 2. Search restaurants by name or cuisine
-- SELECT * FROM restaurants 
-- WHERE search_vector @@ plainto_tsquery('english', 'italian pizza') 
-- ORDER BY rating DESC;

-- 3. Find nearby restaurants (requires lat/lng)
-- SELECT *, 
--        earth_distance(ll_to_earth(latitude, longitude), ll_to_earth(30.2672, -97.7431)) as distance_meters
-- FROM restaurants 
-- WHERE earth_box(ll_to_earth(30.2672, -97.7431), 5000) @> ll_to_earth(latitude, longitude)
-- ORDER BY distance_meters;

-- 4. Get restaurants with specific features
-- SELECT * FROM restaurants WHERE 'delivery' = ANY(features);

-- 5. Analytics query - restaurants by city and vegan status
-- SELECT city, vegan_status, COUNT(*), AVG(rating) 
-- FROM restaurants 
-- GROUP BY city, vegan_status 
-- ORDER BY city, vegan_status;

-- Add some sample data for testing (optional)
INSERT INTO restaurants (
    name, description, city, vegan_status, rating, 
    happycow_url, cuisine_types, features
) VALUES 
(
    'Test Vegan Cafe', 
    'A test restaurant for development', 
    'Austin', 
    'fully vegan', 
    4.5,
    'https://www.happycow.net/test-url-1',
    ARRAY['American', 'Cafe'],
    ARRAY['delivery', 'outdoor seating']
),
(
    'Sample Plant Kitchen', 
    'Another test restaurant', 
    'Austin', 
    'vegan options', 
    4.2,
    'https://www.happycow.net/test-url-2',
    ARRAY['Asian', 'Healthy'],
    ARRAY['takeout', 'vegan desserts']
)
ON CONFLICT (happycow_url) DO NOTHING;

-- Verify the setup
SELECT 
    COUNT(*) as total_restaurants,
    COUNT(DISTINCT city) as cities_covered,
    AVG(rating) as avg_rating
FROM restaurants;