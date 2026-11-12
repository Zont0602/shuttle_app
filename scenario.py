def get_scenario():
    return { 
        "vehicle" : {"id": 10, "capacity" : 4 , "passengers" : 0 , "current_location" : {"lat": 25.03581, "lng": 121.56728}},
        "order" : {"id": 1 , "passengers": 1, "pickup_stop": "s1", "dropoff_stop" :"s2", "status": "requested" , "assigned_vehicle": None},
        "stops" : [
            {"id": "s1" , "name": "松德路1" , "location": {"lat": 25.038444, "lng": 121.576385}},
            {"id": "s2" , "name": "忠孝東路六段1" , "location": {"lat": 25.049906, "lng": 121.592083}}
        ]

    }