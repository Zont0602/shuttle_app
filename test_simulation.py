"""simulation.py 和 sim_state.py 的測試。

執行方式:在專案目錄執行 python3 test_simulation.py
全部通過會印出「全部通過」;有任何一個失敗會在那一行停下並顯示錯誤。
不需要連網,只讀 routes.json。
"""
import json

import sim_state
from simulation import position_on_leg, position_on_route, process_arrivals

with open("routes.json", "r", encoding="utf-8") as file:
    LEGS = json.load(file)["legs"]
LEG = LEGS["vehicle_to_pickup"]


def assert_close(point, expected_lat, expected_lng):
    # 小數有誤差,不能用 ==,改成檢查差距夠小(約 0.2 公尺)
    assert abs(point["lat"] - expected_lat) < 2e-6, point
    assert abs(point["lng"] - expected_lng) < 2e-6, point


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

# 建立狀態時,時鐘從 0 開始,車在路線起點
state = sim_state.create_initial_state(now_s=1000.0)
assert state["sim_time_s"] == 0.0
assert state["vehicle"]["current_location"] == LEG["path"][0]

# 現實過了 10 秒,模擬時鐘也前進 10 秒
sim_state.advance_clock(state, now_s=1010.0)
assert state["sim_time_s"] == 10.0

# 再過 5 秒,累加成 15 秒(不是重新從 0 算)
sim_state.advance_clock(state, now_s=1015.0)
assert state["sim_time_s"] == 15.0

# 更新位置後,車子已經離開起點
sim_state.update_vehicle_location(state)
assert state["vehicle"]["current_location"] != LEG["path"][0]

# 路線依行駛順序排好:第一段的終點 = 第二段的起點
legs = state["route_legs"]
assert legs[0]["path"][-1] == legs[1]["path"][0]

# 每次建立的狀態互不影響(改了一份,另一份不會跟著變)
other = sim_state.create_initial_state(now_s=0.0)
state["order"]["status"] = "onboard"
assert other["order"]["status"] == "assigned"

# 乘客數要等到上車才增加,派車時不變
assert other["vehicle"]["passengers"] == 0


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

# ---------- process_arrivals:到站上下車 ----------


def state_at(sim_time_s, state=None):
    # 把模擬時間設成 sim_time_s 後處理到站事件;沒給 state 就建立新的
    if state is None:
        state = sim_state.create_initial_state(now_s=0.0)
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
assert [event["done"] for event in state["stop_events"]] == [True, False]

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
assert [event["done"] for event in state["stop_events"]] == [True, True]

# 派車的車輛不會因為上下車而改變
assert state["order"]["assigned_vehicle"] == state["vehicle"]["id"]


# 超出允許範圍的倍率會被拒絕
for bad_speed in (0, -1, 100):
    try:
        sim_state.set_speed(bad_speed)
        assert False, f"倍率 {bad_speed} 應該被拒絕"
    except ValueError:
        pass

print("全部通過")
