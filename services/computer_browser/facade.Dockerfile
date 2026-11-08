# Minimal, separate OAuth MCP facade image. No Playwright, owner IAP page,
# browser profiles, private session cookies or Google key files.
FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app PORT=8080
WORKDIR /app
COPY pyproject.toml ./
# Use portable standard Dockerfile shell syntax: Cloud Build's Docker builder does
# not necessarily enable BuildKit heredoc parsing used in local CI.
RUN python -m pip install --no-cache-dir \
    "mcp==2.3.0" \
    "PyJWT[crypto]==2.10.1" \
    "google-auth>=2.30,<3" \
    "httpx>=0.28,<1" \
    "requests>=2.32,<3" \
    "uvicorn==0.34.2"

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
