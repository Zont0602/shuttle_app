"""派車決策:決定訂單交給哪台車。

CLAUDE.md 規定「模擬」與「派車決策」分開寫,所以派車邏輯放在這個檔案,
不放進 simulation.py(模擬車子怎麼移動)。
"""
from route_source import build_route_plan


def dispatch_orders(state):
    order = state["order"]
    vehicle = state["vehicle"]
    if (order["status"] == "requested" 
        and state["sim_time_s"] >= order["request_time_s"] 
        and order["passengers"] + vehicle["passengers"] <= vehicle["capacity"]):
        order["status"] = "assigned"
        order["assigned_vehicle"] = vehicle["id"]
        plan = build_route_plan(state["order"])
        vehicle["route_legs"] = plan["route_legs"]
        vehicle["stop_events"] = plan["stop_events"]
        vehicle["route_start_s"] =  order["request_time_s"]

