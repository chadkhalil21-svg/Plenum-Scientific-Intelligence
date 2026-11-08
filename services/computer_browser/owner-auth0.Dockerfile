# Reuse the EXACT previously-built Plenum Chromium image.
# No new Playwright installation or browser engine build.
FROM us-east1-docker.pkg.dev/plenum-computer-browser/plenum-browser/computer-browser:b078968113f0c688873306258c30f1f7aa662457
USER root
RUN python -m pip install --no-cache-dir \
    "authlib==1.9.5" \
    "httpx==0.28.1" \
    "itsdangerous==2.2.0"
COPY services ./services
RUN chown -R 10001:10001 /srv/plenum/services
USER 10001
EXPOSE 8080
CMD ["python", "-m", "services.computer_browser"]
