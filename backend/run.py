"""
Run script for Seeze Backend API
"""
import uvicorn

def main():
    """Run the FastAPI application"""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=7777,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main() 