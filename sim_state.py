"""模擬狀態:後端記憶體裡「唯一一份」目前世界的樣子。

畫面上的車輛位置、訂單狀態都從這份狀態來(CLAUDE.md 的硬性要求)。
這個檔案只負責「保存狀態、推進時鐘、重設」;怎麼算位置交給 simulation.py。
"""
import copy
import json
import threading
import time
from pathlib import Path

from scenario import get_scenario
from simulation import position_on_route

BASE_DIR = Path(__file__).resolve().parent
ROUTES_FILE = BASE_DIR / "routes.json"

# routes.json 目前用名稱存每段路線;這裡依「行駛順序」轉成 list。
# 之後的程式只看 list 的順序,不看名稱,路線變三段、四段也不用改。
LEG_ORDER = ["vehicle_to_pickup", "pickup_to_dropoff"]

# 鎖:同一時間只讓一個請求讀寫狀態。
# FastAPI 可能同時處理好幾個請求(例如開了兩個分頁在輪詢),
# 沒有鎖的話,兩個請求可能同時推進時鐘,時間會被多算。
_lock = threading.Lock()

# 目前的模擬狀態;第一次被讀取時才建立。
_state = None


def load_route_legs():
    with open(ROUTES_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
    return [data["legs"][name] for name in LEG_ORDER]


def create_initial_state(now_s):
    """建立一份全新的模擬狀態。now_s 是現實時間(秒),用來計算之後經過了多久。"""
    scenario = get_scenario()
    vehicle = scenario["vehicle"]
    order = scenario["order"]

    # 場景前提(暫時):訂單一開始就已派給這台車。
    # 乘客數不變,要等車到上車點才增加(之後的任務處理)。
    order["status"] = "assigned"
    order["assigned_vehicle"] = vehicle["id"]

    state = {
        "sim_time_s": 0.0,            # 模擬時鐘:模擬世界過了幾秒
        "last_real_time_s": now_s,    # 上次推進時鐘時的現實時間
        "vehicle": vehicle,
        "order": order,
        "stops": scenario["stops"],
        "route_legs": load_route_legs(),  # 這台車依序要開的每一段路
    }
    update_vehicle_location(state)
    return state


def advance_clock(state, now_s):
    """把模擬時鐘往前推:現實過了幾秒,模擬就過幾秒。

    之後要做暫停 / 加速,只要改這裡:暫停時不加,加速時乘上倍率。
    """
    real_elapsed_s = now_s - state["last_real_time_s"]
    state["sim_time_s"] += real_elapsed_s
    state["last_real_time_s"] = now_s


def update_vehicle_location(state):
    """依照模擬時鐘,重新計算車輛位置。"""
    state["vehicle"]["current_location"] = position_on_route(
        state["route_legs"], state["sim_time_s"]
    )


def get_current_state():
    """推進時鐘、更新位置,回傳目前狀態的「複本」。"""
    global _state
    with _lock:
        now_s = time.monotonic()
        if _state is None:
            _state = create_initial_state(now_s)
        advance_clock(_state, now_s)
        update_vehicle_location(_state)
        # 回傳複本:FastAPI 把它轉成 JSON 的同時,別的請求可能正在改 _state,
        # 給複本就不會讀到改到一半的資料。
        return copy.deepcopy(_state)


def reset():
    """丟掉目前的模擬,從頭開始。"""
    global _state
    with _lock:
        _state = create_initial_state(time.monotonic())
        return copy.deepcopy(_state)
