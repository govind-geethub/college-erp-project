"""
Entrypoint script for running Prerana College ERP.
Usage:
    python run.py
"""

import uvicorn
import os

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"==================================================")
    print(f" Starting Prerana College ERP System")
    print(f" URL: http://{host}:{port}")
    print(f" College: Bhubaneswar Engineering College")
    print(f" Client: Company A Educational Trust, Bhubaneswar")
    print(f"==================================================")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
