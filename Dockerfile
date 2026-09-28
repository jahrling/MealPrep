FROM python:3.12-slim

WORKDIR /app
COPY server.py dinnertable.html ./

# Run as an unprivileged user; the SQLite file lives on a mounted volume.
RUN useradd --system --uid 10001 app && mkdir /data && chown app /data
USER app

ENV PORT=8002 DB_PATH=/data/mealplan.db PYTHONUNBUFFERED=1
EXPOSE 8002
CMD ["python3", "server.py"]
