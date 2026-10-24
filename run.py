"""Start the Job Cost Tracker web server. Everyone on the LAN can open http://<this-pc>:8000"""

import uvicorn

from app import config

if __name__ == "__main__":
    config.load_env_file()
    uvicorn.run("app.main:app", host=config.host(), port=config.port())
