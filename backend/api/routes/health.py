from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix='/api/health', tags=['health'])

_metrics_engine = None

def init(metrics_engine):
    global _metrics_engine
    _metrics_engine = metrics_engine

@router.get('')
@router.get('/')
async def get_system_health():
    if _metrics_engine is None:
        raise HTTPException(status_code=503, detail="Metrics engine not initialized")
    return _metrics_engine.get_current_health().model_dump(mode='json')

@router.get('/services/{service}')
async def get_service_health(service: str):
    if _metrics_engine is None:
        raise HTTPException(status_code=503, detail="Metrics engine not initialized")
    return _metrics_engine.get_service_health(service).model_dump(mode='json')

@router.get('/history')
async def get_health_history(service: str = Query(...), metric: str = Query('latency_ms'), minutes: int = Query(5)):
    if _metrics_engine is None:
        raise HTTPException(status_code=503, detail="Metrics engine not initialized")
    return _metrics_engine.get_timeseries(service, metric, minutes)
