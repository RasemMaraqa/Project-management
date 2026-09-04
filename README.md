# Project Management API

This is a backend for managing workspaces, projects, tasks, team members,
roles, and permissions. It is built with FastAPI and stores data in
PostgreSQL.

## What you need

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- A `.env` file with your own database settings and `SECRET_KEY`

Before starting the project, create your local configuration file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and replace `your_password` with your own PostgreSQL password.
Also replace `your_secret_key_here` with a strong, unique secret key. Do not
share or commit `.env`.

## Start the project with Docker

1. Copy `.env.example` to `.env` and set your own password and secret key.
2. Open Docker Desktop and wait until the Docker Engine is running.
3. Open PowerShell in this project folder.
4. Start the API and database:

   ```powershell
   docker compose up --build
   ```

5. In a second PowerShell window, create the database tables:

   ```powershell
   docker compose exec api alembic upgrade head
   ```

6. Open `http://localhost:8000/docs` in your browser.

The API runs at `http://localhost:8000`. The `/docs` page is the easiest way
to see every endpoint and send test requests.

The API waits until PostgreSQL is ready before it starts. Database data stays
in a Docker volume, so it remains after you stop the containers.

To stop the stack while keeping data:

```powershell
docker compose down
```

To remove the stack and all Docker-managed database data:

```powershell
docker compose down -v
```

## Run without Docker

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set `DATABASE_URL` to a running PostgreSQL database and set a strong
`SECRET_KEY` in `.env`. Then create the database tables and start the server:

```powershell
alembic upgrade head
uvicorn app.main:app --reload
```

## How to sign in

1. Create a user with `POST /users`.
2. Sign in with `POST /login` using these form fields:

```text
username=<email>
password=<password>
```

3. Copy the access token returned by login. For protected requests, send it
like this:

```text
Authorization: Bearer <access_token>
```

## Main API routes

| Resource | Base routes |
| --- | --- |
| Users and auth | `POST /users`, `POST /login`, `GET /me` |
| Workspaces | `/workspaces` |
| Projects | `/workspaces/{workspace_id}/projects`, `/projects/{project_id}` |
| Tasks | `/projects/{project_id}/tasks` |
| Workspace members | `/workspaces/{workspace_id}/members` |
| Workspace roles | `/workspaces/{workspace_id}/roles` |

Tasks always belong to a project:

```text
GET    /projects/{project_id}/tasks
POST   /projects/{project_id}/tasks
GET    /projects/{project_id}/tasks/{task_id}
PATCH  /projects/{project_id}/tasks/{task_id}
DELETE /projects/{project_id}/tasks/{task_id}
```

Your workspace role controls what you can do with tasks. Viewing, creating,
editing, and deleting tasks each need the matching task permission. A task can
only be assigned to a member of the same workspace.

## Project folders

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

## AI assistance

I used AI assistance for roughly 30% of this project. It helped with planning,
debugging, refactoring, documentation, and review. I assembled, understood,
and tested the project myself.
