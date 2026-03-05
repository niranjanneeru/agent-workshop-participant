# Stage 1: Build the platform frontend
FROM node:20-slim AS frontend-build
WORKDIR /build
RUN corepack enable && corepack prepare yarn@stable --activate
COPY platform/frontend/ ./
RUN yarn install --frozen-lockfile 2>/dev/null || yarn install
RUN yarn build

# Stage 2: Python backend serving the built frontend
FROM python:3.12-slim
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY . .
RUN pip install --no-cache-dir -e .

COPY --from=frontend-build /build/dist ./platform/static/

EXPOSE 8081

CMD ["python", "platform/backend/main.py"]
