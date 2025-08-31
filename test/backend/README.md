# Backend

FastAPI application with Python 3.12+ managed by `uv`.

## Commands

- `uv run poe dev` - Start development server (port 8000)
- `uv run poe test` - Run pytest tests
- `uv run poe lint` - Run ruff linting
- `uv run poe format` - Format code with ruff
- `uv run poe typecheck` - Run mypy type checking


## API Documentation

- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

## Configuration

Environment variables in `.env` file (see `.env.example`).