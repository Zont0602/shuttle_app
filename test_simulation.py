"""simulation.py 和 sim_state.py 的測試。

執行方式:在專案目錄執行 python3 test_simulation.py
全部通過會印出「全部通過」;有任何一個失敗會在那一行停下並顯示錯誤。
不需要連網,只讀 routes.json。
"""
import json

import sim_state
from dispatch import dispatch_orders
from route_source import build_route_plan
from simulation import position_on_leg, position_on_route, process_arrivals

with open("routes.json", "r", encoding="utf-8") as file:
    LEGS = json.load(file)["legs"]
LEG = LEGS["vehicle_to_pickup"]


def assert_close(point, expected_lat, expected_lng):
    # 小數有誤差,不能用 ==,改成檢查差距夠小(約 0.2 公尺)
    assert abs(point["lat"] - expected_lat) < 2e-6, point
    assert abs(point["lng"] - expected_lng) < 2e-6, point


def manually_dispatched_state(route_start_s=0.0):
    # 建立一份「已經派車」的狀態:測試到站、移動時用,不依賴 dispatch_orders。
    # route_start_s 是派車那一刻的模擬時間。
    state = sim_state.create_initial_state(now_s=0.0)
    plan = build_route_plan(state["order"])
    state["vehicle"]["route_legs"] = plan["route_legs"]
    state["vehicle"]["stop_events"] = plan["stop_events"]
    state["vehicle"]["route_start_s"] = route_start_s
    state["order"]["status"] = "assigned"
    state["order"]["assigned_vehicle"] = state["vehicle"]["id"]
    state["sim_time_s"] = route_start_s
    return state


# ---------- position_on_leg ----------

# 0 秒:還沒出發,在起點
assert position_on_leg(LEG, 0) == LEG["path"][0]

# 超過這段的總時間:已到終點
assert position_on_leg(LEG, 999) == LEG["path"][-1]

# 1 秒:在第 0 小段的 39% 處
assert_close(position_on_leg(LEG, 1), 25.035836, 121.567395)

# 75.5 秒(一半時間):在第 20 小段的 91% 處
assert_close(position_on_leg(LEG, 75.5), 25.032651, 121.57247)

# 140 秒:在第 39 小段的 41% 處
assert_close(position_on_leg(LEG, 140), 25.037755, 121.575383)


# ---------- position_on_route ----------

LEG_0 = LEGS["vehicle_to_pickup"]   # 第 0 段:車輛起點 → 上車點(151 秒)
LEG_1 = LEGS["pickup_to_dropoff"]   # 第 1 段:上車點 → 下車點(151.2 秒)
ROUTE = [LEG_0, LEG_1]

# 0 秒:還沒出發,在第 0 段起點
assert position_on_route(ROUTE, 0) == LEG_0["path"][0]

# 100 秒:還在第 0 段,秒數不用換算
assert position_on_route(ROUTE, 100) == position_on_leg(LEG_0, 100)

# 151 秒:剛好走完第 0 段,在上車點(第 0 段終點)
assert position_on_route(ROUTE, 151) == LEG_0["path"][-1]

# 160 秒:進入第 1 段,要換算成這段的第 160 - 151 = 9 秒
# (秒數經過加減換算,可能有極小誤差,所以用 assert_close)
expected = position_on_leg(LEG_1, 9)
assert_close(position_on_route(ROUTE, 160), expected["lat"], expected["lng"])

# 250 秒:第 1 段的第 250 - 151 = 99 秒
expected = position_on_leg(LEG_1, 99)
assert_close(position_on_route(ROUTE, 250), expected["lat"], expected["lng"])

# 超過全部路段的總時間:停在最後一段終點(下車點)
assert position_on_route(ROUTE, 999) == LEG_1["path"][-1]


# ---------- sim_state:模擬時鐘 ----------

# 建立狀態時,時鐘從 0 開始;還沒派車,訂單是 requested,車上沒有路線
state = sim_state.create_initial_state(now_s=1000.0)
assert state["sim_time_s"] == 0.0
assert state["order"]["status"] == "requested"
assert state["order"]["assigned_vehicle"] is None
assert state["vehicle"]["route_legs"] == []
assert state["vehicle"]["stop_events"] == []
assert state["vehicle"]["route_start_s"] is None

# 現實過了 10 秒,模擬時鐘也前進 10 秒
sim_state.advance_clock(state, now_s=1010.0)
assert state["sim_time_s"] == 10.0

# 再過 5 秒,累加成 15 秒(不是重新從 0 算)
sim_state.advance_clock(state, now_s=1015.0)
assert state["sim_time_s"] == 15.0

# 沒有路線時,車子停在原地,位置不變
start_location = state["vehicle"]["current_location"]
sim_state.update_vehicle_location(state)
assert state["vehicle"]["current_location"] == start_location

# 路線依行駛順序排好:第一段的終點 = 第二段的起點
legs = build_route_plan(state["order"])["route_legs"]
assert legs[0]["path"][-1] == legs[1]["path"][0]

# 每次建立的狀態互不影響(改了一份,另一份不會跟著變)
other = sim_state.create_initial_state(now_s=0.0)
state["order"]["status"] = "onboard"
assert other["order"]["status"] == "requested"

# 乘客數要等到上車才增加
assert other["vehicle"]["passengers"] == 0


# ---------- 派車後的移動:位置要扣掉派車時間 ----------

# 第 10 秒派車:派車當下車子在路線起點
state = manually_dispatched_state(route_start_s=10.0)
sim_state.update_vehicle_location(state)
assert state["vehicle"]["current_location"] == LEG["path"][0]

# 模擬第 110 秒 = 派車後開了 100 秒
state["sim_time_s"] = 110.0
sim_state.update_vehicle_location(state)
assert state["vehicle"]["current_location"] == position_on_leg(LEG, 100)


# ---------- sim_state:速度倍率 ----------

# 預設 1 倍速:現實過 10 秒,模擬前進 10 秒
state = sim_state.create_initial_state(now_s=0.0)
assert state["speed"] == 1.0
sim_state.advance_clock(state, now_s=10.0)
assert state["sim_time_s"] == 10.0

# 5 倍速:現實過 2 秒,模擬前進 10 秒
state = sim_state.create_initial_state(now_s=0.0, speed=5)
sim_state.advance_clock(state, now_s=2.0)
assert state["sim_time_s"] == 10.0

# 0.5 倍速:現實過 4 秒,模擬前進 2 秒
state = sim_state.create_initial_state(now_s=0.0, speed=0.5)
sim_state.advance_clock(state, now_s=4.0)
assert state["sim_time_s"] == 2.0

# 中途換倍率:1 倍速走 3 秒,先推進時鐘再換成 10 倍速,再走 1 秒,總共 3 + 10 = 13 秒
# (set_speed 就是這個順序:先用舊倍率推進到現在,才換新倍率)
state = sim_state.create_initial_state(now_s=0.0)
sim_state.advance_clock(state, now_s=3.0)
state["speed"] = 10
sim_state.advance_clock(state, now_s=4.0)
assert state["sim_time_s"] == 13.0

# 現實時間的紀錄不乘倍率
assert state["last_real_time_s"] == 4.0

# ---------- sim_state:暫停 ----------

# 新建立的模擬預設不是暫停
state = sim_state.create_initial_state(now_s=1000.0)
assert state["paused"] is False

# 暫停中,現實過了 10 秒(期間每秒輪詢一次),模擬時間不變
state["sim_time_s"] = 50.0
state["paused"] = True
for now_s in range(1001, 1011):
    sim_state.advance_clock(state, now_s=float(now_s))
assert state["sim_time_s"] == 50.0

# 暫停中,現實時間的紀錄仍然持續更新
assert state["last_real_time_s"] == 1010.0

# 繼續後再過 1 秒,模擬只前進 1 秒(不會把暫停的 10 秒一次補回來)
state["paused"] = False
sim_state.advance_clock(state, now_s=1011.0)
assert state["sim_time_s"] == 51.0

# 暫停中,車子位置和訂單狀態都不變(停在上車點前,不會偷偷上車)
state = manually_dispatched_state(route_start_s=0.0)
state["last_real_time_s"] = 0.0
sim_state.advance_clock(state, now_s=140.0)
sim_state.update_vehicle_location(state)
location_before = state["vehicle"]["current_location"]
state["paused"] = True
sim_state.advance_clock(state, now_s=500.0)
sim_state.update_vehicle_location(state)
process_arrivals(state)
assert state["vehicle"]["current_location"] == location_before
assert state["order"]["status"] == "assigned"
assert state["vehicle"]["passengers"] == 0


# ---------- process_arrivals:到站上下車 ----------


def state_at(sim_time_s, state=None):
    # 把模擬時間設成 sim_time_s 後處理到站事件;沒給 state 就建立「第 0 秒派車」的狀態
    # (派車時間不是 0 的情況,等 process_arrivals 扣掉派車時間後再補測試)
    if state is None:
        state = manually_dispatched_state(route_start_s=0.0)
    state["sim_time_s"] = sim_time_s
    process_arrivals(state)
    return state


# 100 秒:還沒到上車點,訂單仍是 assigned,車上沒人
state = state_at(100)
assert state["order"]["status"] == "assigned"
assert state["vehicle"]["passengers"] == 0

# 151 秒:剛好開完第 0 段,到上車點 → 乘客上車
state = state_at(151, state)
assert state["order"]["status"] == "onboard"
assert state["vehicle"]["passengers"] == 1

# 冪等:同一時間點重複處理 3 次(像重複輪詢),乘客數不會變成 2、3
for _ in range(3):
    state = state_at(151, state)
assert state["vehicle"]["passengers"] == 1

# 200 秒:在去下車點的路上,乘客還在車上(下車事件不可提早執行)
state = state_at(200, state)
assert state["order"]["status"] == "onboard"
assert state["vehicle"]["passengers"] == 1
assert [event["done"] for event in state["vehicle"]["stop_events"]] == [True, False]

# 302.2 秒:開完第 1 段,到下車點 → 乘客下車,訂單完成
state = state_at(302.2, state)
assert state["order"]["status"] == "completed"
assert state["vehicle"]["passengers"] == 0

# 完成後再處理,不會變成負數
state = state_at(400, state)
assert state["vehicle"]["passengers"] == 0

# 時間一次跳過兩個站(例如 10 倍速 + 每秒輪詢):上下車依序都要執行
state = state_at(100)
state = state_at(400, state)
assert state["order"]["status"] == "completed"
assert state["vehicle"]["passengers"] == 0
assert [event["done"] for event in state["vehicle"]["stop_events"]] == [True, True]

# 派車的車輛不會因為上下車而改變
assert state["order"]["assigned_vehicle"] == state["vehicle"]["id"]


# ---------- dispatch_orders:派車 ----------

# 還沒到叫車時間(第 10 秒):不派車,訂單維持 requested,車上沒有路線
state = sim_state.create_initial_state(now_s=0.0)
state["sim_time_s"] = 9.9
dispatch_orders(state)
assert state["order"]["status"] == "requested"
assert state["vehicle"]["route_legs"] == []

# 到了叫車時間:派車,路線和事件交給車輛,記下派車時間
state["sim_time_s"] = 10.0
dispatch_orders(state)
assert state["order"]["status"] == "assigned"
assert state["order"]["assigned_vehicle"] == state["vehicle"]["id"]
assert len(state["vehicle"]["route_legs"]) == 2
assert len(state["vehicle"]["stop_events"]) == 2
assert state["vehicle"]["route_start_s"] == 10.0

# 派車不會改乘客數(要等到站才上車)
assert state["vehicle"]["passengers"] == 0

# 冪等:之後重複呼叫(像重複輪詢),不會重新派車,派車時間不會被改掉
state["sim_time_s"] = 20.0
dispatch_orders(state)
dispatch_orders(state)
assert state["vehicle"]["route_start_s"] == 10.0

# 第 10 秒派車:到站時間要扣掉派車時間
# 上車點在 10 + 151 = 161 秒,下車點在 10 + 302.2 = 312.2 秒
for sim_time_s, expected_status, expected_passengers in [
    (160, "assigned", 0),     # 車子還在去接人的路上,不能提早上車
    (161, "onboard", 1),      # 到上車點
    (312.1, "onboard", 1),    # 還差一點才到下車點
    (312.2, "completed", 0),  # 到下車點
]:
    state["sim_time_s"] = sim_time_s
    process_arrivals(state)
    assert state["order"]["status"] == expected_status, sim_time_s
    assert state["vehicle"]["passengers"] == expected_passengers, sim_time_s

# 還沒派車時處理到站事件,不會出錯,也不會改變任何狀態
state = sim_state.create_initial_state(now_s=0.0)
process_arrivals(state)
assert state["order"]["status"] == "requested"
assert state["vehicle"]["passengers"] == 0

# 可重現:模擬時間一次跳過叫車時間(例如 20 倍速 + 每秒輪詢),
# 派車時間仍是叫車時間 10 秒,不是「剛好輪詢到的時間」;位置與到站結果也一樣
for first_poll_s in (36.7, 150, 170):
    state = sim_state.create_initial_state(now_s=0.0)
    state["sim_time_s"] = first_poll_s
    dispatch_orders(state)
    sim_state.update_vehicle_location(state)
    process_arrivals(state)
    assert state["vehicle"]["route_start_s"] == 10, first_poll_s
    expected = position_on_route(state["vehicle"]["route_legs"], first_poll_s - 10)
    assert state["vehicle"]["current_location"] == expected, first_poll_s
# 170 秒時已經過了上車時間(161 秒),第一次輪詢就要完成派車並讓乘客上車
assert state["order"]["status"] == "onboard"
assert state["vehicle"]["passengers"] == 1

# 坐不下時不派車:車上已滿,訂單維持 requested
state = sim_state.create_initial_state(now_s=0.0)
state["vehicle"]["passengers"] = state["vehicle"]["capacity"]
state["sim_time_s"] = 10.0
dispatch_orders(state)
assert state["order"]["status"] == "requested"
assert state["vehicle"]["route_legs"] == []


# 超出允許範圍的倍率會被拒絕
for bad_speed in (0, -1, 100):
    try:
        sim_state.set_speed(bad_speed)
        assert False, f"倍率 {bad_speed} 應該被拒絕"
    except ValueError:
        pass

print("全部通過")
