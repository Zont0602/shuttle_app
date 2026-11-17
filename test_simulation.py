"""simulation.py 和 sim_state.py 的測試。

執行方式:在專案目錄執行 python3 test_simulation.py
全部通過會印出「全部通過」;有任何一個失敗會在那一行停下並顯示錯誤。
不需要連網,只讀 routes.json。
"""
import json

import sim_state
from simulation import position_on_leg

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

print("全部通過")
