#!/usr/bin/env python
import os

import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=8585,
        reload=os.getenv("WORKER_RELOAD", "false").lower() == "true",
    )
