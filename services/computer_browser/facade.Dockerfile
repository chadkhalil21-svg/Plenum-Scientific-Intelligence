# A separate small OAuth MCP facade image. It does NOT contain Playwright,
# browser storage, cookies, Google service account key files, or owner IAP UI.
FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app PORT=8080
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN python -m pip install --no-cache-dir -e '.[browser_mcp]'
COPY services/computer_browser ./services/computer_browser
RUN useradd --uid 10001 --create-home --no-log-init plenum && \
    chown -R 10001:10001 /app
USER 10001:10001
EXPOSE 8080
CMD ["sh","-c","exec uvicorn services.computer_browser.oauth_asgi:app --host 0.0.0.0 --port \"$PORT\" --proxy-headers --forwarded-allow-ips 127.0.0.1"]
