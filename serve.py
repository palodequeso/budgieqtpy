from backend import Server

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(Server.app, host="0.0.0.0", port=8000)
