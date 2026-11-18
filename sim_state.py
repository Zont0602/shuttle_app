"""模擬狀態:後端記憶體裡「唯一一份」目前世界的樣子。

畫面上的車輛位置、訂單狀態都從這份狀態來(CLAUDE.md 的硬性要求)。
這個檔案只負責「保存狀態、推進時鐘、重設」;怎麼算位置交給 simulation.py。
"""
import copy
import threading
import time

from dispatch import dispatch_orders
from scenario import get_scenario
from simulation import position_on_route, process_arrivals

# 鎖:同一時間只讓一個請求讀寫狀態。
# FastAPI 可能同時處理好幾個請求(例如開了兩個分頁在輪詢),
# 沒有鎖的話,兩個請求可能同時推進時鐘,時間會被多算。
_lock = threading.Lock()

# 目前的模擬狀態;第一次被讀取時才建立。
_state = None

# 模擬速度倍率的允許範圍:1 = 正常速度,2 = 兩倍快,0.5 = 一半慢。
MIN_SPEED = 0.1
MAX_SPEED = 20


def create_initial_state(now_s, speed=1.0):
    """建立一份全新的模擬狀態。now_s 是現實時間(秒),用來計算之後經過了多久。"""
    scenario = get_scenario()
    vehicle = scenario["vehicle"]
    order = scenario["order"]   # 一開始是 requested,要等 dispatch_orders 派車

    # 派車前,車上沒有任何路線,停在原地。派車時由 dispatch_orders 填入。
    vehicle["route_legs"] = []       # 這台車依序要開的每一段路
    vehicle["stop_events"] = []      # 這台車依序要執行的上下車事件
    vehicle["route_start_s"] = None  # 開始跑這條路線時的模擬時間(派車那一刻)

    state = {
        "sim_time_s": 0.0,            # 模擬時鐘:模擬世界過了幾秒
        "last_real_time_s": now_s,    # 上次推進時鐘時的現實時間
        "speed": speed,               # 模擬速度倍率:現實 1 秒 = 模擬幾秒
        "paused": False,              # 是否暫停:暫停時模擬時鐘不前進
        "vehicle": vehicle,
        "order": order,
        "stops": scenario["stops"],
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
    vehicle = state["vehicle"]
    if not vehicle["route_legs"]:
        return  # 還沒派車,沒有路線:停在原地,位置不變

    # 車子沿這條路線已經開了幾秒 = 現在的模擬時間 - 派車時的模擬時間
    driven_s = state["sim_time_s"] - vehicle["route_start_s"]
    vehicle["current_location"] = position_on_route(vehicle["route_legs"], driven_s)


def _bring_state_up_to_now(now_s):
    """確保狀態存在,並把時鐘和車輛位置更新到現在。呼叫前必須已經拿到鎖。"""
    global _state
    if _state is None:
        _state = create_initial_state(now_s)
    advance_clock(_state, now_s)       # 1. 時間往前推
    dispatch_orders(_state)            # 2. 有沒有該派車的訂單(先派車,下一步才會用新路線算位置)
    update_vehicle_location(_state)    # 3. 車子在哪
    process_arrivals(_state)           # 4. 有沒有到站,到了就上下車


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
