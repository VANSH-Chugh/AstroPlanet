from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json
import re

from app.astro_engine import generate_chart

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")



@app.get("/")
def serve_home():
    return FileResponse("static/index.html")

class BirthInput(BaseModel):
    name: str
    dob: str
    time: str
    lat: float
    lon: float

def sanitize_filename(name: str):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name.strip())

@app.post("/generate")
def generate(data: BirthInput):
    result = generate_chart(
        dob=data.dob,
        time_str=data.time,
        lat=data.lat,
        lon=data.lon
    )

    safe_name = sanitize_filename(data.name)

    return Response(
        content=json.dumps(result, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}_planetary_data.json"'
        }
    )