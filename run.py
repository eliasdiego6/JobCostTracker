"""Start the Job Cost Tracker web server. Everyone on the LAN can open http://<this-pc>:8000"""

import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=os.environ.get("JCT_HOST", "0.0.0.0"), port=int(os.environ.get("JCT_PORT", "8000")))
