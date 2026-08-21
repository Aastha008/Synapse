from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix='/api/incidents', tags=['incidents'])

_repository = None
_root_cause_analyzer = None


def init(repository, root_cause_analyzer):
    global _repository, _root_cause_analyzer
    _repository = repository
    _root_cause_analyzer = root_cause_analyzer


@router.get('')
@router.get('/')
async def list_incidents(limit: int = Query(20), severity: str | None = Query(None)):
    if _repository is None:
        raise HTTPException(status_code=503, detail="Repository not initialized")
    incidents = await _repository.get_recent_incidents(limit=limit, severity=severity)
    return incidents  # already dicts from repository


@router.get('/active')
async def get_active_incidents():
    if _repository is None:
        raise HTTPException(status_code=503, detail="Repository not initialized")
    incidents = await _repository.get_active_incidents()
    return incidents  # already dicts from repository


@router.get('/{incident_id}')
async def get_incident(incident_id: str):
    if _repository is None:
        raise HTTPException(status_code=503, detail="Repository not initialized")
    incident = await _repository.get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident  # already a dict from repository
