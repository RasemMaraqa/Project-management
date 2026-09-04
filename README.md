# Project Management API

A FastAPI REST API for managing workspaces, projects, tasks, members, roles,
and permissions. PostgreSQL is used for persistence and Alembic manages schema
migrations.

## Stack

- Python and FastAPI
- SQLAlchemy
- PostgreSQL 16
- Alembic
- Docker Compose

## Run with Docker

1. Install and start [Docker Desktop](https://www.docker.com/products/docker-desktop/).
   Wait until the Docker Engine is running.
2. Create a `.env` file in the project root with the database and application
   settings. Do not commit this file.
3. Start the API and database:

   ```powershell
   docker compose up --build
   ```

4. Apply migrations after the services are running:

   ```powershell
   docker compose exec api alembic upgrade head
   ```

The API is available at `http://localhost:8000`. Interactive API
documentation is available at `http://localhost:8000/docs`.

The `db` service has a PostgreSQL healthcheck. The API waits until the
database is healthy before it starts. Database data is stored in the named
`postgres_data` volume and therefore survives container restarts.

To stop the stack while keeping data:

```powershell
docker compose down
```

To remove the stack and all Docker-managed database data:

```powershell
docker compose down -v
```

## Local development

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set `DATABASE_URL` to a reachable PostgreSQL database and set a strong
`SECRET_KEY` in `.env`. Apply migrations and start the development server:

```powershell
alembic upgrade head
uvicorn app.main:app --reload
```

## Authentication

Create a user with `POST /users`, then obtain a bearer token with
`POST /login` using form fields:

```text
username=<email>
password=<password>
```

Include the result in protected requests:

```text
Authorization: Bearer <access_token>
```

## API overview

| Resource | Base routes |
| --- | --- |
| Users and auth | `POST /users`, `POST /login`, `GET /me` |
| Workspaces | `/workspaces` |
| Projects | `/workspaces/{workspace_id}/projects`, `/projects/{project_id}` |
| Tasks | `/projects/{project_id}/tasks` |
| Workspace members | `/workspaces/{workspace_id}/members` |
| Workspace roles | `/workspaces/{workspace_id}/roles` |

Task routes are project-scoped:

```text
GET    /projects/{project_id}/tasks
POST   /projects/{project_id}/tasks
GET    /projects/{project_id}/tasks/{task_id}
PATCH  /projects/{project_id}/tasks/{task_id}
DELETE /projects/{project_id}/tasks/{task_id}
```

Task access is authorized through workspace membership and the corresponding
task permission: `TASK_VIEW`, `TASK_CREATE`, `TASK_UPDATE`, or `TASK_DELETE`.
When assigning a task, the assignee must be a member of that task's workspace.

## Project structure

```text
app/
├── authorization/  # Roles, permissions, and authorization policies
├── core/           # Configuration and security utilities
├── database/       # SQLAlchemy session setup
├── dependencies/   # Reusable FastAPI dependencies
├── models/         # SQLAlchemy entities
├── routers/        # HTTP endpoints grouped by resource
├── schemas/        # Pydantic request and response contracts
└── main.py         # Application assembly and top-level endpoints
alembic/             # Database migration scripts
docker-compose.yml   # API and PostgreSQL services
Dockerfile           # FastAPI container image
```
