from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

import config
from database.db import init_db
from database.repository import Repository
from pipeline.queue import EventQueue
from pipeline.processor import LogProcessor
from simulator.log_generator import LogGenerator
from analytics.metrics_engine import MetricsEngine
from analytics.anomaly_detector import AnomalyDetector
from analytics.root_cause_analyzer import RootCauseAnalyzer

from api.websocket import WebSocketManager
from api.routes.health import router as health_router, init as init_health
from api.routes.incidents import router as incident_router, init as init_incidents
from api.routes.metrics import router as metrics_router, init as init_metrics
from api.routes.logs import router as logs_router, init as init_logs

async def health_broadcast_task(ws_manager, metrics_engine):
    interval = getattr(config, 'HEALTH_BROADCAST_INTERVAL_SECONDS', 5)
    while True:
        try:
            health = metrics_engine.get_current_health()
            await ws_manager.broadcast_health(health)
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.error(f"Error in health broadcast task: {e}")
            await asyncio.sleep(interval)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('main')
    
    logger.info("Initializing database...")
    await init_db()
    
    logger.info("Creating components...")
    queue = EventQueue()
    repository = Repository()
    metrics_engine = MetricsEngine()
    anomaly_detector = AnomalyDetector()
    root_cause_analyzer = RootCauseAnalyzer()
    ws_manager = WebSocketManager()
    
    logger.info("Initializing route dependencies...")
    init_health(metrics_engine)
    init_incidents(repository, root_cause_analyzer)
    init_metrics(metrics_engine)
    init_logs(repository)
    
    logger.info("Starting LogProcessor...")
    processor = LogProcessor(queue, repository, metrics_engine, anomaly_detector, root_cause_analyzer, ws_manager)
    processor_task = asyncio.create_task(processor.start())
    
    logger.info("Starting LogGenerator...")
    generator = LogGenerator(queue)
    generator_task = asyncio.create_task(generator.start())
    
    logger.info("Starting Queue...")
    queue_task = asyncio.create_task(queue.start())
    
    app.state.ws_manager = ws_manager
    app.state.generator = generator
    app.state.metrics_engine = metrics_engine
    app.state.repository = repository
    
    logger.info("Starting health broadcast task...")
    broadcast_task = asyncio.create_task(health_broadcast_task(ws_manager, metrics_engine))
    
    yield
    
    # SHUTDOWN
    logger.info("Shutting down...")
    broadcast_task.cancel()
    processor_task.cancel()
    generator_task.cancel()
    queue_task.cancel()
    
    # Attempt proper shutdown if available
    try:
        await generator.stop()
    except Exception:
        pass
    try:
        await queue.stop()
    except Exception:
        pass

app = FastAPI(
    title='Synapse — AI Observability & Root Cause Intelligence',
    description='Real-time event-driven incident detection and AI root cause analysis',
    version='1.0.0',
    lifespan=lifespan,
)

cors_origins = getattr(config, 'CORS_ORIGINS', ['*'])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Include routers
app.include_router(health_router)
app.include_router(incident_router)
app.include_router(metrics_router)
app.include_router(logs_router)

@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    ws_manager = app.state.ws_manager
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == 'trigger_incident':
                await app.state.generator.trigger_incident('db_connection_exhaustion')
            elif data == 'reset':
                await app.state.generator.reset()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)

@app.get('/api/scenario/trigger')
async def trigger_scenario(name: str = Query('db_connection_exhaustion')):
    # Depending on implementation, trigger_incident could be sync or async
    result = app.state.generator.trigger_incident(name)
    if asyncio.iscoroutine(result):
        await result
    return {'status': 'triggered', 'scenario': name}

@app.get('/api/scenario/reset')
async def reset_scenario():
    result = app.state.generator.reset()
    if asyncio.iscoroutine(result):
        await result
    if hasattr(app.state, 'metrics_engine'):
        app.state.metrics_engine.reset()
    if hasattr(app.state, 'repository'):
        try:
            db = await app.state.repository.get_active_incidents()
            # update status in db if needed
            from database.db import get_connection
            conn = await get_connection()
            await conn.execute("UPDATE incidents SET status = 'RESOLVED' WHERE status = 'ACTIVE'")
            await conn.commit()
        except Exception:
            pass
    return {'status': 'reset'}
