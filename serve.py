import os
from backend.server import Server

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))

    print("=" * 60)
    print("Starting Budgie Backend API (Service-Based Architecture)")
    print("=" * 60)
    print(f"API Documentation: http://localhost:{port}/docs")
    print(f"Frontend: http://localhost:{port}")
    print("=" * 60)

    uvicorn.run(Server.app, host="0.0.0.0", port=port)
