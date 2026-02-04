import uvicorn
import os

def run_app():
    print("Starting Premium Reminder Web App on http://localhost:8000")
    # Make sure we use the correct path to the app
    uvicorn.run("admin.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    run_app()
