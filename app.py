import json
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from main import assign_order
from scenario import get_scenario

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
ROUTES_FILE = BASE_DIR / "routes.json"

app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@lru_cache(maxsize=1)
def load_routes():
    with open(ROUTES_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def build_state():
    state = get_scenario()
    vehicle = state["vehicle"]
    order = state["order"]

    assigned_id = assign_order([vehicle], order["passengers"])
    if assigned_id is None:
        order["status"] = "unassigned"
        return state

    order["status"] = "assigned"
    order["assigned_vehicle"] = assigned_id
    state["routes"] = load_routes()["legs"]
    return state


@app.get("/api/state")
def get_state():
    return build_state()


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
