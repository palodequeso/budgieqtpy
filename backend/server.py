import os
from typing import Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.profile import ProfileAPI
from api.schedule import ScheduleAPI
from database.database import Database

# from api.routes import router

class Server:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/profiles/{profile_id}")
    async def get_profile(profile_id):
        db = Database()
        profile_api = ProfileAPI(db)
        profile = profile_api.get_profile_by_id(int(profile_id))
        if not profile:
            return {"error": f"Profile with id {profile_id} not found."}
        return profile

    @app.get("/profiles")
    async def get_profiles():
        db = Database()
        profile_api = ProfileAPI(db)
        profiles = profile_api.get_profiles()
        return profiles

    @app.get("/schedule/{profile_id}")
    async def get_schedule(profile_id):
        db = Database()
        schedule_api = ScheduleAPI(db)
        schedule = schedule_api.get_by_profile_id(int(profile_id))
        return schedule

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
