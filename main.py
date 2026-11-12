import json
import yaml


def can_accept_order(vehicle, new_passengers):
    return new_passengers >0 and vehicle["passengers"] + new_passengers <= vehicle["capacity"]

    
def assign_order(vehicles, new_passengers, extra_minutes=None,pickup_minutes=None,max_extra_minutes=None):
    if extra_minutes is not None:
        best_id = select_vehicle(vehicles, new_passengers, extra_minutes, pickup_minutes, max_extra_minutes=max_extra_minutes)
        for vehicle in vehicles:
            if vehicle["id"] == best_id:
                vehicle["passengers"] += new_passengers
                return vehicle["id"]
        return None
    else:
        for vehicle in vehicles:
            if can_accept_order(vehicle, new_passengers):
                vehicle["passengers"] += new_passengers
                return vehicle["id"]
        return None

def load_vehicles(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data,dict):
        raise ValueError("車輛資料最外層必須是字典")
    vehicles = data["vehicles"]
    seen_ids = set()
    
    if not isinstance(vehicles, list):
        raise ValueError("vehicles 必須是清單")
    for vehicle in vehicles:
        if not isinstance(vehicle , dict):
            raise ValueError("每台車輛必須是字典")
        if "passengers" not in vehicle:
            raise ValueError("車輛缺少passengers欄位")
        if type(vehicle["passengers"]) is not int:
            raise ValueError("passengers 必須是整數")
        if vehicle["passengers"] < 0 :
            raise ValueError("passengers 不可小於 0")
        if "capacity" not in vehicle:
            raise ValueError("車輛缺少capacity欄位")
        if type(vehicle["capacity"]) is not int:
            raise ValueError("capacity 必須是整數")
        if vehicle["capacity"] <= 0 :
            raise ValueError("capacity 必須大於 0")
        if vehicle["passengers"] > vehicle["capacity"] :
            raise ValueError("passengers 不可超過 capacity")
        if "id" not in vehicle:
            raise ValueError("車輛缺少id欄位")
        if type(vehicle["id"]) is not int:
            raise ValueError("id 必須是整數")
        if vehicle["id"] <= 0 :
            raise ValueError("id 必須大於 0")
        if vehicle["id"] in seen_ids:
            raise ValueError("車輛 id 不可重複")
        seen_ids.add(vehicle["id"])

    return vehicles

def save_vehicles(file_path, vehicles):
    data_to_save = {"vehicles":vehicles}
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data_to_save, file, indent=4)

def select_vehicle(vehicles, new_passengers, extra_minutes, pickup_minutes = None, max_extra_minutes = None):
    best_id = None
    for vehicle in vehicles:
        current_vehicle_id = vehicle["id"]
        if current_vehicle_id not in extra_minutes:
            continue
        if max_extra_minutes is not None and extra_minutes[current_vehicle_id]  > max_extra_minutes:
            continue
        if can_accept_order(vehicle,new_passengers):
            if best_id is None:
                best_id = current_vehicle_id
            elif extra_minutes[current_vehicle_id] < extra_minutes[best_id] :
                best_id = current_vehicle_id
            elif (pickup_minutes is not None
                  and current_vehicle_id in pickup_minutes
                  and best_id in pickup_minutes):
                if extra_minutes[current_vehicle_id] == extra_minutes[best_id] :
                    if pickup_minutes[current_vehicle_id] < pickup_minutes[best_id]:
                        best_id = current_vehicle_id
    return best_id

def load_max_extra_minutes(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    if not isinstance(config,dict):
        raise ValueError("設定檔最外層必須是字典")
    vehicle_config = config["vehicle"]
    if not isinstance(vehicle_config,dict):
        raise ValueError("vehicle 設定必須是字典")
    max_extra_minutes = vehicle_config["max_extra_minutes"]
    if type(max_extra_minutes) is not int or max_extra_minutes < 0 :
        raise ValueError("最大繞路時間必須是非負整數")
    return max_extra_minutes

def calculate_extra_minutes(original_minutes, proposed_minutes):
    return proposed_minutes - original_minutes

def build_extra_minutes(original_minutes, proposed_minutes):
    extra_minutes = {}
    for vehicle_id in original_minutes :
        extra_minutes[vehicle_id] = calculate_extra_minutes(original_minutes[vehicle_id],proposed_minutes[vehicle_id] )
    return extra_minutes

def can_serve_on_route(route, order):
    pickup_stop = order["pickup_stop"]
    dropoff_stop = order["dropoff_stop"]
    if pickup_stop in route and dropoff_stop in route:
        if route.index(pickup_stop) < route.index(dropoff_stop):
            return True
    return False
    
if __name__ == "__main__":
    
    try:
        max_extra_minutes = load_max_extra_minutes("config.yaml")
    except ValueError as error:
        raise SystemExit(f"設定錯誤：{error}")
    except FileNotFoundError:
        raise SystemExit("設定錯誤：找不到設定檔")
    except yaml.YAMLError:
        raise SystemExit("設定錯誤 : YAML 格式不正確")
    except KeyError:
        raise SystemExit("設定錯誤：缺少必要欄位")

    print(max_extra_minutes)

    file_path = "test_vehicles.json"
    try:
        vehicles = load_vehicles(file_path)
    except FileNotFoundError :
        print("找不到車輛資料檔案")
    except json.JSONDecodeError:
        print("車輛資料格式錯誤")
    except KeyError:
        print("車輛資料缺少必要欄位")
    except ValueError as error:
        print(error)
    else:
        print("車輛資料讀取成功")
        for vehicle in vehicles:
            print(f"車輛{vehicle['id']}: 剩餘{vehicle['capacity'] - vehicle['passengers']}個座位 ")
        user_input = input("請輸入乘客人數:")
        try:
            new_passengers = int(user_input)
        except ValueError :
            print("請輸入整數")
        else :
            if new_passengers <= 0:
                print("乘客人數必須大於 0")
            else:

                original_minutes = {10: 18, 20: 15}
                proposed_minutes = {10: 23, 20: 18}
                extra_minutes = build_extra_minutes(original_minutes,proposed_minutes)
                pickup_minutes ={
                                    10 : 4,
                                    20 : 2
                                }
                result = assign_order(vehicles, new_passengers,extra_minutes,pickup_minutes,max_extra_minutes=max_extra_minutes)
                if result is None:
                    print("目前沒有可承接的車輛")
                else :
                    print(f"已安排車輛 {result}, 預估該車輛增加行車時間: {extra_minutes[result]} 分鐘")
                    pickup_eta = pickup_minutes.get(result)
                    if pickup_eta is None :
                        print("暫無上車時間估算")
                    else:
                        print(f"預計 {pickup_eta} 分鐘後上車")
                    save_vehicles(file_path,vehicles)
                    for vehicle in vehicles:
                        if vehicle["id"] == result:
                            print(f"剩餘{vehicle['capacity'] - vehicle['passengers']}個座位")
                            break

                        
