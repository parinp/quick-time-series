"""
Entry point for running the FastAPI application
"""
import uvicorn

if __name__ == "__main__":
    # Run the app with uvicorn
    # Using app.main:app (the app variable inside app/main.py)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True) 