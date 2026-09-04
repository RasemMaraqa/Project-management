# Project-management

## Application structure

```text
app/
├── authorization/  # Roles, permissions, and authorization policies
├── core/           # Configuration and security utilities
├── database/       # Database session setup and seed commands
├── dependencies/   # Reusable FastAPI dependency resolvers
├── models/         # SQLAlchemy entities
├── routers/        # HTTP endpoints grouped by resource
├── schemas/        # Pydantic request and response contracts
└── main.py         # Application assembly and top-level endpoints
```

Each package exposes its supported public objects through `__init__.py`. This
keeps imports concise (for example, `from app.database import get_db`) while
leaving implementation details in focused modules such as `session.py` and
`contracts.py`.
