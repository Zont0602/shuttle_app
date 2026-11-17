def position_on_leg(leg, elapsed_s):
    distance_m = leg["distance_m"]
    duration_s = leg["duration_s"]
    if elapsed_s <= 0 :
        return leg["path"][0]
    if elapsed_s >= duration_s:
        return leg["path"][-1]
    speed = distance_m/duration_s
    traveled_m = speed * elapsed_s
    total_len = 0
    for i , seg_m in  enumerate(leg["segment_distances_m"]) :
        total_len += seg_m
        if traveled_m <= total_len :
            ratio = (traveled_m + seg_m - total_len) / seg_m
            start_point = leg["path"][i]
            end_point = leg["path"][i+1]   
            start_point_lat = start_point["lat"]    
            start_point_lng = start_point["lng"]    
            end_point_lat = end_point["lat"]    
            end_point_lng = end_point["lng"] 
            return {"lat" : start_point_lat + (end_point_lat - start_point_lat)*ratio , "lng" : start_point_lng + (end_point_lng - start_point_lng)*ratio}
    return leg["path"][-1]


def position_on_route(route_legs, elapsed_s):
    total_s = 0
    for leg in route_legs :
        total_s += leg["duration_s"]
        if total_s >= elapsed_s :
            s_on_leg = leg["duration_s"] - (total_s - elapsed_s) 
            return position_on_leg(leg , s_on_leg)
    return position_on_leg(route_legs[-1], elapsed_s)
