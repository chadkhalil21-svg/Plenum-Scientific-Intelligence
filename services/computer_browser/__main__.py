"""Container startup, no self-managed model or GPU."""
import os
import uvicorn

if __name__ == "__main__":
    uvicorn.run("services.computer_browser.api:app",host="0.0.0.0",
                port=int(os.environ.get("PORT", "8080")),log_level="warning",
                proxy_headers=False)
