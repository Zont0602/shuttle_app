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
from simulation import position_on_route, process_arrivals

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

# 模擬速度倍率的允許範圍:1 = 正常速度,2 = 兩倍快,0.5 = 一半慢。
MIN_SPEED = 0.1
MAX_SPEED = 20


def load_route_legs():
    with open(ROUTES_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
    return [data["legs"][name] for name in LEG_ORDER]


def create_initial_state(now_s, speed=1.0):
    """建立一份全新的模擬狀態。now_s 是現實時間(秒),用來計算之後經過了多久。"""
    scenario = get_scenario()
    vehicle = scenario["vehicle"]
    order = scenario["order"]

    # 場景前提(暫時):訂單一開始就已派給這台車。
    # 乘客數不變,要等車到上車點才增加(由 process_arrivals 處理)。
    order["status"] = "assigned"
    order["assigned_vehicle"] = vehicle["id"]

    # 到站事件:依發生順序排列。
    # leg_index 表示「開完第幾段 leg 時」發生這個事件(從 0 開始)。
    # done 表示這個事件是否已經執行過;執行過的事件不能再執行一次。
    stop_events = [
        {"type": "pickup", "order_id": order["id"], "stop_id": order["pickup_stop"],
         "leg_index": 0, "done": False},
        {"type": "dropoff", "order_id": order["id"], "stop_id": order["dropoff_stop"],
         "leg_index": 1, "done": False},
    ]

    state = {
        "sim_time_s": 0.0,            # 模擬時鐘:模擬世界過了幾秒
        "last_real_time_s": now_s,    # 上次推進時鐘時的現實時間
        "speed": speed,               # 模擬速度倍率:現實 1 秒 = 模擬幾秒
        "paused": False,              # 是否暫停:暫停時模擬時鐘不前進
        "vehicle": vehicle,
        "order": order,
        "stops": scenario["stops"],
        "route_legs": load_route_legs(),  # 這台車依序要開的每一段路
        "stop_events": stop_events,       # 這台車依序要執行的上下車事件
    }
    update_vehicle_location(state)
    return state


def advance_clock(state, now_s):
    """把模擬時鐘往前推:模擬前進的秒數 = 現實經過的秒數 × 速度倍率。

    暫停時不加模擬時間,但 last_real_time_s 照常更新,
    這樣繼續之後不會把暫停期間的時間一次補回來。
    """
    real_elapsed_s = now_s - state["last_real_time_s"]
    if not state["paused"] :
        state["sim_time_s"] += real_elapsed_s * state["speed"]
    state["last_real_time_s"] = now_s


def update_vehicle_location(state):
    """依照模擬時鐘,重新計算車輛位置。"""
    state["vehicle"]["current_location"] = position_on_route(
        state["route_legs"], state["sim_time_s"]
    )


def _bring_state_up_to_now(now_s):
    """確保狀態存在,並把時鐘和車輛位置更新到現在。呼叫前必須已經拿到鎖。"""
    global _state
    if _state is None:
        _state = create_initial_state(now_s)
    advance_clock(_state, now_s)
    update_vehicle_location(_state)
    process_arrivals(_state)


def get_current_state():
    """推進時鐘、更新位置,回傳目前狀態的「複本」。"""
    with _lock:
        _bring_state_up_to_now(time.monotonic())
        # 回傳複本:FastAPI 把它轉成 JSON 的同時,別的請求可能正在改 _state,
        # 給複本就不會讀到改到一半的資料。
        return copy.deepcopy(_state)


def set_speed(speed):
    """改變模擬速度倍率。"""
    if not (MIN_SPEED <= speed <= MAX_SPEED):
        raise ValueError(f"速度倍率必須介於 {MIN_SPEED} 和 {MAX_SPEED} 之間")
    with _lock:
        # 先用「舊的倍率」把時鐘推進到現在,再換新倍率。
        # 不先推進的話,上次輪詢到現在這段時間會被誤用新倍率重算。
        _bring_state_up_to_now(time.monotonic())
        _state["speed"] = speed
        return copy.deepcopy(_state)


def set_paused(paused):
    """暫停(paused=True)或繼續(paused=False)模擬。重複暫停或重複繼續都不會出錯。"""
    with _lock:
        # 和 set_speed 一樣:先把時鐘推進到現在,再切換。
        # 暫停時:按下暫停前跑的那一小段時間要算進去。
        # 繼續時:暫停期間的時間在這裡被「跳過」,不會在繼續後一次補回來。
        _bring_state_up_to_now(time.monotonic())
        _state["paused"] = paused
        return copy.deepcopy(_state)


def reset():
    """丟掉目前的模擬,從頭開始。速度倍率保留;暫停會解除,重設後直接開始跑。"""
    global _state
    with _lock:
        speed = _state["speed"] if _state is not None else 1.0
        _state = create_initial_state(time.monotonic(), speed)
        return copy.deepcopy(_state)
