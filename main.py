from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import Optional
from dotenv import load_dotenv

# 在本機開發時，放一個 `.env` 並寫入 MONGODB_URI=...，load_dotenv() 會載入它
load_dotenv()

# 由環境變數提供連線字串（部署在 Render 時請在 Environment variables 填入）
# 不建議把使用者/密碼硬編在程式碼內。
MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME", "emogo_db")

app = FastAPI()

# 掛載 static 目錄以提供 CSS/JS 等靜態檔案
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 templates
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup_db_client():
    if not MONGODB_URI:
        raise RuntimeError("MONGODB_URI not set. 在本機請建立 .env，或在部署平台設定 MONGODB_URI 環境變數。")
    app.mongodb_client = AsyncIOMotorClient(MONGODB_URI)
    app.mongodb = app.mongodb_client[DB_NAME]


@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()


@app.get("/items")
async def get_items():
    items = await app.mongodb["records"].find().to_list(100)
    return items


@app.get("/export", response_class=HTMLResponse)
async def export_page(request: Request):
        # 使用 Jinja2 模板渲染 dashboard；模板在 templates/export.html
        items = await app.mongodb["records"].find().to_list(100)
        return templates.TemplateResponse("export.html", {"request": request, "items": items})


@app.get("/export.csv")
async def export_csv():
    # 產生 CSV 並回傳為附件，包含 latitude/longitude
    items = await app.mongodb["records"].find().to_list(1000)
    import io, csv

    output = io.StringIO()
    writer = csv.writer(output)
    # header
    writer.writerow(["_id", "user_id", "score", "video_url", "latitude", "longitude"])
    for it in items:
        _id = str(it.get("_id", ""))
        user_id = it.get("user_id") or it.get("userid") or it.get("user") or ""
        score = it.get("score", "")
        video = it.get("video_url") or it.get("video") or it.get("videoUrl") or ""
        latitude = it.get("latitude", "")
        longitude = it.get("longitude", "")
        writer.writerow([_id, user_id, score, video, latitude, longitude])

    data = output.getvalue().encode("utf-8")
    return StreamingResponse(io.BytesIO(data), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=export.csv"})
