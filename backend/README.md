# AVAP Backend

Automated Vulnerability Assessment Platform — Backend Service.

## Prerequisites

- Python 3.12+
- PostgreSQL 15+
- Nmap (for scanner integration)

## Setup

1. **Create virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

2. **Install dependencies:**

   ```bash
   pip install -e ".[dev]"
   ```

3. **Configure environment:**

   ```bash
   cp .env.example .env
   # Edit .env with actual database credentials
   ```

4. **Run database migrations:**

   ```bash
   alembic upgrade head
   ```

5. **Start the application:**

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Running Tests

```bash
pytest
```

## API Documentation

Once running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

See `project_structure.md` for the complete directory layout.
