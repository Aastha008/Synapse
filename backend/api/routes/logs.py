from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix='/api/logs', tags=['logs'])

_repository = None


def init(repository):
    global _repository
    _repository = repository


@router.get('')
@router.get('/')
async def get_logs(
    service: str | None = Query(None),
    level: str | None = Query(None),
    limit: int = Query(100),
):
    if _repository is None:
        raise HTTPException(status_code=503, detail="Repository not initialized")
    logs = await _repository.get_recent_logs(service=service, level=level, limit=limit)
    return logs  # already dicts from repository
