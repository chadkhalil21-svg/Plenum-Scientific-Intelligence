# Minimal, separate OAuth MCP facade image. No Playwright, owner IAP page,
# browser profiles, private session cookies or Google key files.
FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app PORT=8080
WORKDIR /app
COPY pyproject.toml ./
RUN python - <<'PY'
import subprocess
import sys
import tomllib
with open("pyproject.toml", "rb") as f:
    requirements=tomllib.load(f)["project"]["optional-dependencies"]["browser_mcp"]
subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", *requirements])
PY
RUN mkdir -p /app/services/computer_browser
COPY services/__init__.py ./services/__init__.py
COPY services/computer_browser/__init__.py ./services/computer_browser/__init__.py
COPY services/computer_browser/oauth_resource_boundary.py ./services/computer_browser/oauth_resource_boundary.py
COPY services/computer_browser/mcp_resource_server.py ./services/computer_browser/mcp_resource_server.py
COPY services/computer_browser/oauth_asgi.py ./services/computer_browser/oauth_asgi.py
RUN useradd --uid 10001 --create-home --no-log-init plenum && chown -R 10001:10001 /app
USER 10001:10001
EXPOSE 8080
CMD ["sh","-c","exec uvicorn services.computer_browser.oauth_asgi:app --host 0.0.0.0 --port \"$PORT\" --proxy-headers --forwarded-allow-ips 127.0.0.1"]
