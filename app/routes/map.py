import math
from flask import Blueprint, request, jsonify
from app.models import db, Constituency  # Added db import just in case

spatial_bp = Blueprint('spatial', __name__)

@spatial_bp.route('/api/spatial/nearby-constituencies', methods=['GET'])
def get_nearby_constituencies():
    # 1. Parse query parameters with sensible fallbacks (Defaults to Lusaka & 600km radius)
    try:
        user_lat = float(request.args.get('lat', -15.4167))
        user_lng = float(request.args.get('lng', 28.2833))
        radius_km = float(request.args.get('radius', 600.0))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid coordinate or radius formatting"}), 400

    earth_radius = 6371.0  # Earth's radius in Kilometers
    
    # 2. Coarse Filter: Calculate Bounding Box Deltas
    # Converts distance into degree thresholds to leverage standard SQL index scanning
    lat_delta = (radius_km / earth_radius) * (180.0 / math.pi)
    
    # Prevent math domain error if user_lat gets too close to the poles (unlikely for Zambia, but good practice!)
    cos_lat = math.cos(math.radians(user_lat))
    if abs(cos_lat) < 0.001:
        cos_lat = 0.001
        
    lng_delta = (radius_km / earth_radius) * (180.0 / math.pi) / cos_lat
    
    min_lat, max_lat = user_lat - lat_delta, user_lat + lat_delta
    min_lng, max_lng = user_lng - lng_delta, user_lng + lng_delta
    
    # 3. Database Execution: Fast Range Filter
    try:
        candidates = Constituency.query.filter(
            Constituency.latitude.between(min_lat, max_lat),
            Constituency.longitude.between(min_lng, max_lng)
        ).all()
    except Exception as e:
        return jsonify({"error": "Database query failed", "details": str(e)}), 500
    
    # 4. Fine Filter: Calculate Exact Distance via Haversine & Build GeoJSON Collection
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    for c in candidates:
        # Skip if entry is corrupted or missing geospatial points
        if c.latitude is None or c.longitude is None:
            continue
            
        dlat = math.radians(c.latitude - user_lat)
        dlng = math.radians(c.longitude - user_lng)
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(math.radians(user_lat)) * math.cos(math.radians(c.latitude)) * math.sin(dlng / 2) ** 2)
        angular_distance = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        exact_distance = earth_radius * angular_distance
        
        # If it falls within the exact circular boundary, package it into GeoJSON format
        if exact_distance <= radius_km:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [c.longitude, c.latitude]  # Strict GeoJSON standard: [lng, lat]
                },
                "properties": {
                    "id": c.id,
                    "name": c.name,
                    "district_id": c.district_id,
                    "distance_km": round(exact_distance, 2)
                }
            }
            geojson["features"].append(feature)
            
    return jsonify(geojson)