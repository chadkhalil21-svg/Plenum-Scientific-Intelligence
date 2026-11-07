FROM mcr.microsoft.com/playwright/python:v1.64.1-noble
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
WORKDIR /srv/plenum
COPY pyproject.toml ./
COPY src ./src
RUN python -m pip install --no-cache-dir -e '.[browser,browser_secure,browser_cloud_storage]' fastapi==0.115.12 uvicorn==0.34.2
COPY services ./services
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin browser \
    && chown -R 10001:10001 /srv/plenum
USER 10001
EXPOSE 8080
CMD ["python", "-m", "services.computer_browser"]
