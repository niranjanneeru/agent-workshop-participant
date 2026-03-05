# Stage 1: Build the React frontend
FROM node:20-slim AS frontend-build
WORKDIR /build
COPY evaluation/frontend/package.json evaluation/frontend/package-lock.json ./
RUN npm ci
COPY evaluation/frontend/ ./
RUN npm run build

# Stage 2: Python backend serving the built frontend
FROM python:3.12-slim
WORKDIR /app

COPY evaluation/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY evaluation/backend/ ./backend/
COPY evaluation/checkpoints.yaml ./checkpoints.yaml
COPY --from=frontend-build /build/dist ./static/

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
