# Reuse the EXACT previously-built Plenum Chromium image.
# No new Playwright installation or browser engine build.
FROM us-east1-docker.pkg.dev/plenum-computer-browser/plenum-browser/computer-browser:b078968113f0c688873306258c30f1f7aa662457
# Keep private owner page data and tasks out of upstream telemetry and file logs.
ENV ANONYMIZED_TELEMETRY=false BROWSER_USE_SETUP_LOGGING=false
USER root
RUN python -m pip install --no-cache-dir \
    "fastapi==0.115.12" \
    "authlib==1.9.5" \
    "httpx==0.28.1" \
    "itsdangerous==2.2.0" \
    "websockets==15.0.1" \
    "browser-use==0.13.14"
# The prebuilt Chromium base pins uvicorn==0.34.2 but not the optional
# WebSocket protocol. Without websockets/wsproto, real HTTP Upgrades are
# rejected even though in-memory FastAPI TestClient websocket tests pass.
RUN python -c "import importlib.metadata as m; import browser_use; import uvicorn, websockets; assert m.version('playwright') == '1.64.1'; assert m.version('browser-use') == '0.13.14'; assert uvicorn.__version__ == '0.34.2'; assert websockets.__version__ == '15.0.1'"
COPY services ./services
# Fail the build before Cloud Run if dependency changes break the actual app.
RUN python -m pip check && python -c "from services.computer_browser.api import app; assert app"
RUN chown -R 10001:10001 /srv/plenum/services
USER 10001
EXPOSE 8080
CMD ["python", "-m", "services.computer_browser"]
