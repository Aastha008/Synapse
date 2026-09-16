from fastapi import APIRouter, Query, HTTPException

from database.mongo_repository import get_raw_logs_for_incident

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


@router.get('/{incident_id}/raw-logs')
async def get_incident_raw_logs(incident_id: str, limit: int = Query(25)):
    """Raw, non-normalized log payloads for this incident's affected services,
    pulled from the Mongo archive — for a frontend 'view raw evidence' drill-down."""
    if _repository is None:
        raise HTTPException(status_code=503, detail="Repository not initialized")
    incident = await _repository.get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    raw_logs = await get_raw_logs_for_incident(
        services=incident.get("affected_services", []),
        around=incident.get("detected_at"),
        limit=limit,
    )
    return {"incident_id": incident_id, "raw_logs": raw_logs}
