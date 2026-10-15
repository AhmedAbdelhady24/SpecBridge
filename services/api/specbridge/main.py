import os
import secrets
import stat
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from .models import Project, ProjectCreate, Revision, RevisionEdit, Source, SourceCreate
from .storage import Conflict, NotFound, Store

LOOPBACK = {"localhost", "127.0.0.1", "::1"}


def local_token(data_dir: Path) -> str:
    data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = data_dir / "session-token"
    if path.is_symlink():
        raise ValueError("Session token must be a regular private file")
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if not stat.S_ISREG(path.stat().st_mode) or path.stat().st_mode & 0o077:
            raise ValueError("Session token file must have owner-only permissions")
        token = path.read_text().strip()
        if len(token) < 32:
            raise ValueError("Invalid session token file")
        return token
    token = secrets.token_urlsafe(32)
    with os.fdopen(fd, "w") as file:
        file.write(token)
    return token


def error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        {"error": {"code": code, "message": message}}, status_code=status
    )


def create_app(*, data_dir: Path, token: str, allowed_origin: str) -> FastAPI:
    origin = urlsplit(allowed_origin)
    if (
        origin.scheme != "http"
        or origin.hostname not in LOOPBACK
        or origin.path
        or origin.query
        or origin.fragment
        or origin.username
    ):
        raise ValueError("UI origin must be an exact loopback HTTP origin")
    if not token:
        raise ValueError("Local session token is required")
    app = FastAPI(
        title="SpecBridge",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    store = Store(data_dir / "specbridge.db")
    app.state.store = store

    @app.exception_handler(NotFound)
    async def not_found(request: Request, exc: NotFound) -> JSONResponse:
        return error(404, "not_found", "Project resource not found")

    @app.exception_handler(Conflict)
    async def conflict(request: Request, exc: Conflict) -> JSONResponse:
        return error(409, "conflict", str(exc))

    @app.exception_handler(ValueError)
    async def bad_value(request: Request, exc: ValueError) -> JSONResponse:
        return error(422, "invalid_input", "Input violates project constraints")

    @app.middleware("http")
    async def local_boundary(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            host = urlsplit("http://" + request.headers.get("host", "")).hostname
        except ValueError:
            host = None
        if (
            host not in LOOPBACK
            or request.headers.get("origin", allowed_origin) != allowed_origin
        ):
            return error(
                403, "forbidden_origin", "Only the configured local UI is allowed"
            )
        if request.url.path.startswith("/api/") and request.url.path != "/api/health":
            supplied = request.headers.get("authorization", "")
            if not secrets.compare_digest(
                supplied.encode(), ("Bearer " + token).encode()
            ):
                return error(401, "unauthorized", "Enter the local session token")
        size = 0
        chunks = []
        async for chunk in request.stream():
            size += len(chunk)
            if size > 512 * 1024:
                return error(
                    413, "body_too_large", "Request exceeds the local input limit"
                )
            chunks.append(chunk)
        request._body = b"".join(chunks)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_input(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return error(422, "invalid_input", "Request does not match the required schema")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/config")
    def config() -> dict[str, Any]:
        return {
            "provider": "fixture",
            "model": "demo",
            "destination": "local fixture (no network)",
        }

    @app.get("/api/projects")
    def projects() -> list[Project]:
        return store.projects()

    @app.post("/api/projects", status_code=201)
    def create_project(body: ProjectCreate) -> Project:
        return store.create_project(body.name)

    @app.post("/api/projects/{project_id}/sources", status_code=201)
    def create_source(project_id: str, body: SourceCreate) -> Source:
        return store.add_source(project_id, body.text)

    @app.get("/api/projects/{project_id}/revisions/{revision_id}")
    def revision(project_id: str, revision_id: str) -> Revision:
        return store.get_revision(project_id, revision_id)

    @app.post(
        "/api/projects/{project_id}/revisions/{revision_id}/edits", status_code=201
    )
    def edit(project_id: str, revision_id: str, body: RevisionEdit) -> Revision:
        previous = store.get_revision(project_id, revision_id)
        if previous.digest != body.expected_digest:
            raise Conflict("Revision changed; reload before editing")
        return store.save_revision(project_id, body.artifact, body.expected_digest)

    return app


def create_default_app() -> FastAPI:
    data_dir = Path(os.environ.get("SPECBRIDGE_DATA_DIR", ".data"))
    return create_app(
        data_dir=data_dir,
        token=os.environ.get("SPECBRIDGE_TOKEN") or local_token(data_dir),
        allowed_origin=os.environ.get("SPECBRIDGE_UI_ORIGIN", "http://127.0.0.1:5173"),
    )
