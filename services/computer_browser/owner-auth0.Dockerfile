# Reuse the EXACT previously-built Plenum Chromium image.
# No new Playwright installation or browser engine build.
FROM us-east1-docker.pkg.dev/plenum-computer-browser/plenum-browser/computer-browser:b078968113f0c688873306258c30f1f7aa662457
USER root
RUN python -m pip install --no-cache-dir \
    "authlib==1.9.5" \
    "httpx==0.28.1" \
    "itsdangerous==2.2.0" \
    "websockets==13.1"
# The prebuilt Chromium base pins uvicorn==0.34.2 but not the optional
# WebSocket protocol. Without websockets/wsproto, real HTTP Upgrades are
# rejected even though in-memory FastAPI TestClient websocket tests pass.
RUN python -c "import uvicorn, websockets; assert uvicorn.__version__ == '0.34.2'; assert websockets.__version__ == '13.1'"
COPY services ./services
RUN chown -R 10001:10001 /srv/plenum/services
USER 10001
EXPOSE 8080
CMD ["python", "-m", "services.computer_browser"]
