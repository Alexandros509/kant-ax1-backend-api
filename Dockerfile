FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app

# 의존성만 먼저 설치 (코드가 바뀌어도 이 층은 캐시 재사용)
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src

CMD [".venv/bin/uvicorn", "main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
