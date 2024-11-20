from bson import ObjectId
from django.http import JsonResponse
from django.middleware.csrf import get_token
from pymongo import MongoClient
import os
import math
import json
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv('DB_URI'))
db = client.cafe_db
collection = db.stores

def get_csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)})

RADIUS_KM = 1

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def get_nearby_data(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')

            if latitude is None or longitude is None:
                return JsonResponse({"error": "Latitude and longitude are required"}, status=400)

            results = []
            for item in collection.find():
                coordinates = item.get('coordinates')
                if not coordinates or 'lat' not in coordinates or 'lng' not in coordinates:
                    continue

                item_lat = coordinates['lat']
                item_lng = coordinates['lng']
                distance = haversine_distance(latitude, longitude, item_lat, item_lng)

                if distance <= RADIUS_KM * 1000:
                    # ObjectIdを文字列に変換
                    item['_id'] = str(item['_id'])
                    item['distance'] = distance
                    results.append(item)

            return JsonResponse({
                "message": "近くの店舗",
                "latitude": latitude,
                "longitude": longitude,
                "results": results
            }, safe=False)
        else:
            return JsonResponse({"error": "Invalid method"}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        print(f"Error in get_nearby_data: {e}")
        return JsonResponse({"error": str(e)}, status=500)
