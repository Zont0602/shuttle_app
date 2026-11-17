from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

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


class SpeedRequest(BaseModel):
    # 請求內容的格式:{"speed": 2}
    # FastAPI 會自動檢查:缺欄位、不是數字、超出範圍,都會回傳 422 和錯誤說明
    speed: float = Field(ge=sim_state.MIN_SPEED, le=sim_state.MAX_SPEED)


@app.post("/api/speed")
def set_speed(request: SpeedRequest):
    # 改變模擬速度倍率(快轉 / 放慢)
    return sim_state.set_speed(request.speed)


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
