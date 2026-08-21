from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix='/api/metrics', tags=['metrics'])

_metrics_engine = None


def init(metrics_engine):
    global _metrics_engine
    _metrics_engine = metrics_engine


@router.get('/timeseries')
async def get_timeseries(
    service: str = Query(...),
    metric: str = Query('latency_ms'),
    minutes: int = Query(5),
):
    if _metrics_engine is None:
        raise HTTPException(status_code=503, detail="Metrics engine not initialized")
    ts = _metrics_engine.get_timeseries(service, metric, minutes)
    return ts.model_dump(mode='json')


@router.get('/summary')
async def get_metrics_summary():
    if _metrics_engine is None:
        raise HTTPException(status_code=503, detail="Metrics engine not initialized")
    return _metrics_engine.get_current_health().model_dump(mode='json')


@router.get('/errors')
async def get_error_distribution():
    if _metrics_engine is None:
        raise HTTPException(status_code=503, detail="Metrics engine not initialized")
    dist = _metrics_engine.get_error_distribution()
    return [d.model_dump(mode='json') for d in dist]


@router.get('/all-timeseries')
async def get_all_timeseries(minutes: int = Query(5)):
    if _metrics_engine is None:
        raise HTTPException(status_code=503, detail="Metrics engine not initialized")
    all_ts = _metrics_engine.get_all_timeseries(minutes)
    # Serialize: {service: {metric: MetricTimeSeries}} -> JSON-safe dict
    result = {}
    for svc, metrics in all_ts.items():
        result[svc] = {}
        for metric_name, ts in metrics.items():
            result[svc][metric_name] = ts.model_dump(mode='json')
    return result
