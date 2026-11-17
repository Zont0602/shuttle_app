from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import sim_state

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/api/state")
def get_state():
    # 讀取目前的模擬狀態(會先把模擬時鐘推進到現在)
    return sim_state.get_current_state()


@app.post("/api/reset")
def reset_state():
    # 重設模擬:時鐘歸零、車回到起點
    return sim_state.reset()


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
