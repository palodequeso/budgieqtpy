from backend.server import Server

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("Starting Budgie Backend API (Service-Based Architecture)")
    print("=" * 60)
    print("API Documentation: http://localhost:8000/docs")
    print("Frontend: http://localhost:8000")
    print("=" * 60)
    
    uvicorn.run(Server.app, host="0.0.0.0", port=8000)
