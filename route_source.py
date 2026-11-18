"""路線來源:提供「某張訂單要開哪些路線」。

CLAUDE.md 規定路線來源要保持獨立介面,日後可以替換。
目前從預先查好的 routes.json 讀取,不連網;之後換成別的來源時,只改這個檔案。
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROUTES_FILE = BASE_DIR / "routes.json"

# routes.json 目前用名稱存每段路線;這裡依「行駛順序」轉成 list。
# 之後的程式只看 list 的順序,不看名稱,路線變三段、四段也不用改。
LEG_ORDER = ["vehicle_to_pickup", "pickup_to_dropoff"]


def load_route_legs():
    with open(ROUTES_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
    return [data["legs"][name] for name in LEG_ORDER]


def build_route_plan(order):
    """回傳接送這張訂單要開的路線,以及沿途要執行的上下車事件。

    限制(暫時):routes.json 只有這一張訂單的路線,而且是從車輛初始位置查的。
    階段 3 要改成依「車輛當下位置」和「訂單的站點」取得路線。
    """
    route_legs = load_route_legs()

    # 到站事件:依發生順序排列。
    # leg_index 表示「開完第幾段 leg 時」發生這個事件(從 0 開始)。
    # done 表示這個事件是否已經執行過;執行過的事件不能再執行一次。
    stop_events = [
        {"type": "pickup", "order_id": order["id"], "stop_id": order["pickup_stop"],
         "leg_index": 0, "done": False},
        {"type": "dropoff", "order_id": order["id"], "stop_id": order["dropoff_stop"],
         "leg_index": 1, "done": False},
    ]
    return {"route_legs": route_legs, "stop_events": stop_events}
