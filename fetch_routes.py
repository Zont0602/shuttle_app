import json
import time
import urllib.request
from datetime import datetime, timezone

from scenario import get_scenario

OSRM_BASE = "https://router.project-osrm.org/route/v1/driving"


def fetch_leg(start, end):
    # OSRM 要「經度,緯度」,所以 lng 在前
    coords = f"{start['lng']},{start['lat']};{end['lng']},{end['lat']}"
    # annotations=distance:另外回傳「相鄰兩個座標點之間」的距離(公尺)
    url = f"{OSRM_BASE}/{coords}?overview=full&geometries=geojson&annotations=distance"
    request = urllib.request.Request(url, headers={"User-Agent": "shuttle-app-demo"})
    with urllib.request.urlopen(request, timeout=10) as response:
        data = json.load(response)
    if data.get("code") != "Ok":
        raise RuntimeError(f"OSRM 回傳錯誤: {data.get('code')}")
    route = data["routes"][0]
    # GeoJSON 的座標是 [經度, 緯度],轉成有名字的欄位
    path = [{"lat": lat, "lng": lng} for lng, lat in route["geometry"]["coordinates"]]
    # 只查兩個點,所以只會有一段 leg;它的 annotation 存著每一小段的距離
    segment_distances_m = route["legs"][0]["annotation"]["distance"]

    # N 個座標點之間有 N-1 小段;數量對不上代表資料有問題,不要存檔
    if len(segment_distances_m) != len(path) - 1:
        raise RuntimeError(
            f"小段距離數量不符:{len(segment_distances_m)} 段,但有 {len(path)} 個座標點"
        )

    return {
        "distance_m": route["distance"],
        "duration_s": route["duration"],
        "path": path,
        "segment_distances_m": segment_distances_m,
    }


def main():
    scenario = get_scenario()
    stops = {stop["id"]: stop["location"] for stop in scenario["stops"]}
    order = scenario["order"]
    start = scenario["vehicle"]["current_location"]
    pickup = stops[order["pickup_stop"]]
    dropoff = stops[order["dropoff_stop"]]

    result = {
        "source": "OSRM public demo server",
        "profile": "driving",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "legs": {},
    }
    result["legs"]["vehicle_to_pickup"] = fetch_leg(start, pickup)
    time.sleep(1)
    result["legs"]["pickup_to_dropoff"] = fetch_leg(pickup, dropoff)

    with open("routes.json", "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2, ensure_ascii=False)

    for name, leg in result["legs"].items():
        print(name, leg["distance_m"], "公尺", leg["duration_s"], "秒", len(leg["path"]), "個座標點")


if __name__ == "__main__":
    main()