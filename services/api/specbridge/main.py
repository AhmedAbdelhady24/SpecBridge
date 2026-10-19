import os
import secrets
import stat
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from .delivery_routes import register_delivery_routes
from .feature_history import FeatureHistory, FeatureRevision, RevisionComparison
from .git_routes import register_git_routes
from .knowledge import register_knowledge_routes
from .models import (
    AdvanceRequest,
    ApprovalCreate,
    Candidate,
    Project,
    ProjectCreate,
    ProviderInfo,
    Review,
    ReviewCreate,
    Revision,
    RevisionEdit,
    Run,
    RunCreate,
    RunSummary,
    Source,
    SourceCreate,
    SourceSummary,
)
from .providers import FixtureProvider, Provider, provider_from_env
from .publication import Publication
from .skills import SkillMetadata, SkillRegistry
from .storage import Conflict, NotFound, Store
from .workbench_models import PackagePreview
from .workbench_routes import register_workbench_routes
from .workflow import Workflow

LOOPBACK = {"localhost", "127.0.0.1", "::1"}
ROOT = Path(__file__).resolve().parents[3]


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


def create_app(
    *,
    data_dir: Path,
    token: str,
    allowed_origin: str,
    provider: Provider | None = None,
    skill_root: Path | None = None,
    template_root: Path | None = None,
) -> FastAPI:
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
    register_knowledge_routes(app, store)
    register_workbench_routes(app, store)
    configured_provider = provider or FixtureProvider()
    registry = SkillRegistry(skill_root or ROOT / "skills/runtime")
    workflow = Workflow(store, registry, configured_provider)
    publication = Publication(store, template_root or ROOT / "packages/docs-template")
    register_git_routes(app, store, publication)
    register_delivery_routes(app, store)

    @app.exception_handler(StarletteHTTPException)
    async def http_failure(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return error(
            exc.status_code,
            "not_found" if exc.status_code == 404 else "http_error",
            "Resource not found"
            if exc.status_code == 404
            else "Request could not be completed",
        )

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
    def config() -> ProviderInfo:
        return ProviderInfo.model_validate(
            {
                "provider": configured_provider.mode,
                "model": configured_provider.model,
                "destination": configured_provider.destination,
            }
        )

    @app.get("/api/projects")
    def projects() -> list[Project]:
        return store.projects()

    @app.post("/api/projects", status_code=201)
    def create_project(body: ProjectCreate) -> Project:
        return store.create_project(body.name)

    @app.post("/api/projects/{project_id}/sources", status_code=201)
    def create_source(project_id: str, body: SourceCreate) -> Source:
        return store.add_source(project_id, body.text)

    @app.get("/api/projects/{project_id}/sources")
    def sources(
        project_id: str,
        query: str = Query(default="", max_length=200),
        limit: int = Query(default=20, ge=1, le=50),
        after: str | None = Query(default=None, max_length=100),
    ) -> list[SourceSummary]:
        with store.transaction() as db:
            store.require_project(db, project_id)
            after_rowid = 0
            if after:
                cursor = db.execute(
                    "SELECT rowid FROM sources WHERE project_id=? AND id=? "
                    "AND json_extract(data,'$.knowledge_ref') IS NULL "
                    "AND coalesce(json_extract(data,'$.kind'),'user_provided')='user_provided'",
                    (project_id, after),
                ).fetchone()
                if not cursor:
                    raise NotFound("Source cursor not found")
                after_rowid = cursor[0]
            result = []
            # casefold supplies Unicode-aware literal matching; no LIKE wildcards.
            for row in db.execute(
                "SELECT data FROM sources WHERE project_id=? AND rowid>? "
                "AND json_extract(data,'$.knowledge_ref') IS NULL "
                "AND coalesce(json_extract(data,'$.kind'),'user_provided')='user_provided' "
                "ORDER BY rowid",
                (project_id, after_rowid),
            ):
                item = Source.model_validate_json(row[0])
                if query.casefold() not in item.text.casefold():
                    continue
                result.append(
                    SourceSummary(
                        id=item.id,
                        project_id=project_id,
                        digest=item.digest,
                        preview=item.text[:320],
                    )
                )
                if len(result) == limit:
                    break
            return result

    @app.get("/api/projects/{project_id}/sources/{source_id}")
    def source(project_id: str, source_id: str) -> Source:
        return store.sources(project_id, [source_id])[0]

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
        with store.transaction() as db:
            association = db.execute(
                "SELECT run_id FROM revision_lineage WHERE revision_id=? AND project_id=?",
                (revision_id, project_id),
            ).fetchone()
            if not association:
                raise Conflict(
                    "Historical feature association is unknown; this revision is read-only"
                )
            revised = store.save_revision(
                project_id,
                body.artifact,
                body.expected_digest,
                run_id=association[0],
                parent_revision_id=revision_id,
                findings=workflow.findings(body.artifact),
                connection=db,
            )
            for row in db.execute(
                "SELECT id,data FROM runs WHERE project_id=?", (project_id,)
            ).fetchall():
                run = Run.model_validate_json(row["data"])
                if run.revision_id == revision_id:
                    run.revision_id = revised.id
                    run.stage = "human_review"
                    run.status = "review"
                    db.execute(
                        "UPDATE runs SET data=? WHERE id=?",
                        (run.model_dump_json(), run.id),
                    )
        return revised

    @app.get("/api/skills")
    def skills(intent: str = "") -> list[SkillMetadata]:
        if len(intent) > 2000:
            raise ValueError("Intent too long")
        return registry.search(intent)

    @app.post("/api/projects/{project_id}/runs", status_code=201)
    def start_run(project_id: str, body: RunCreate) -> Run:
        return workflow.start(
            project_id,
            body.source_ids,
            body.intent,
            body.skill_id,
            body.acknowledged_destination,
        )

    @app.get("/api/projects/{project_id}/runs")
    def runs(project_id: str) -> list[RunSummary]:
        return workflow.list_runs(project_id)

    @app.get("/api/projects/{project_id}/runs/{run_id}/history")
    def feature_history(
        project_id: str,
        run_id: str,
        before: int | None = Query(default=None, ge=1),
        limit: int = Query(default=20, ge=1, le=50),
    ) -> list[FeatureRevision]:
        return FeatureHistory(store).list(project_id, run_id, before, limit)

    @app.get("/api/projects/{project_id}/runs/{run_id}/compare")
    def compare_revisions(
        project_id: str,
        run_id: str,
        base: str = Query(max_length=128),
        head: str = Query(max_length=128),
    ) -> RevisionComparison:
        return FeatureHistory(store).compare(project_id, run_id, base, head)

    @app.get("/api/projects/{project_id}/runs/{run_id}")
    def get_run(project_id: str, run_id: str) -> Run:
        return workflow.get(project_id, run_id)

    @app.post("/api/projects/{project_id}/runs/{run_id}/advance", response_model=Run)
    def advance(
        project_id: str, run_id: str, body: AdvanceRequest
    ) -> Run | JSONResponse:
        run = workflow.advance(
            project_id, run_id, retry_acknowledged=body.retry_acknowledged
        )
        if run.status == "failed":
            return error(
                502,
                run.error or "stage_failed",
                "Workflow stage failed; inspect saved state before an explicit retry",
            )
        return run

    @app.get("/api/projects/{project_id}/revisions/{revision_id}/reviews")
    def reviews(project_id: str, revision_id: str) -> list[Review]:
        return publication.reviews(project_id, revision_id)

    @app.post(
        "/api/projects/{project_id}/revisions/{revision_id}/reviews", status_code=201
    )
    def review(project_id: str, revision_id: str, body: ReviewCreate) -> Review:
        return publication.review(project_id, revision_id, body.disposition, body.notes)

    @app.post(
        "/api/projects/{project_id}/revisions/{revision_id}/candidates", status_code=201
    )
    def prepare(project_id: str, revision_id: str) -> Candidate:
        return publication.prepare(project_id, revision_id)

    @app.get("/api/projects/{project_id}/candidates/{candidate_id}/preview")
    def preview_package(
        project_id: str,
        candidate_id: str,
        path: str | None = Query(default=None, max_length=200),
    ) -> PackagePreview:
        return publication.preview(project_id, candidate_id, path)

    @app.post("/api/projects/{project_id}/candidates/{candidate_id}/approve")
    def approve(project_id: str, candidate_id: str, body: ApprovalCreate) -> Candidate:
        return publication.approve(project_id, candidate_id, body.digest)

    @app.get(
        "/api/projects/{project_id}/candidates/{candidate_id}/download",
        responses={
            200: {
                "content": {
                    "application/zip": {
                        "schema": {"type": "string", "format": "binary"}
                    }
                }
            }
        },
    )
    def download(project_id: str, candidate_id: str) -> Response:
        return Response(
            publication.download(project_id, candidate_id),
            media_type="application/zip",
            headers={
                "Content-Disposition": 'attachment; filename="specbridge-documentation.zip"'
            },
        )

    web = ROOT / "apps/web/dist"
    if (web / "index.html").is_file():
        app.mount("/assets", StaticFiles(directory=web / "assets"), name="assets")

        @app.get("/", include_in_schema=False)
        def index() -> FileResponse:
            return FileResponse(web / "index.html")

    return app


def create_default_app() -> FastAPI:
    data_dir = Path(os.environ.get("SPECBRIDGE_DATA_DIR", ".data"))
    return create_app(
        data_dir=data_dir,
        token=os.environ.get("SPECBRIDGE_TOKEN") or local_token(data_dir),
        allowed_origin=os.environ.get("SPECBRIDGE_UI_ORIGIN", "http://127.0.0.1:5173"),
        provider=provider_from_env(),
    )
