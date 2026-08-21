import json
from datetime import datetime
from typing import Optional
from database.db import get_connection
from models.schemas import LogEvent, Metric, Incident, Evidence, IncidentStatus, Severity, LogLevel

class Repository:
    async def insert_log(self, log: LogEvent) -> None:
        db = await get_connection()
        await db.execute(
            '''INSERT INTO logs (id, timestamp, service, level, message, latency_ms, status_code, trace_id, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (log.id, log.timestamp.isoformat(), log.service, log.level.value, log.message, 
             log.latency_ms, log.status_code, log.trace_id, json.dumps(log.metadata))
        )
        await db.commit()

    async def insert_metric(self, metric: Metric) -> None:
        db = await get_connection()
        await db.execute(
            '''INSERT INTO metrics (timestamp, service, metric_name, value)
               VALUES (?, ?, ?, ?)''',
            (metric.timestamp.isoformat(), metric.service, metric.metric_name, metric.value)
        )
        await db.commit()

    async def insert_incident(self, incident: Incident) -> None:
        db = await get_connection()
        await db.execute(
            '''INSERT INTO incidents (id, detected_at, severity, title, root_cause, confidence, affected_services, evidence, recommended_actions, status, deployment_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (incident.id, incident.detected_at.isoformat(), incident.severity.value, incident.title, incident.root_cause,
             incident.confidence, json.dumps(incident.affected_services), json.dumps([e.model_dump(mode='json') for e in incident.evidence]),
             json.dumps(incident.recommended_actions), incident.status.value, incident.deployment_version)
        )
        await db.commit()

    async def get_recent_logs(self, service: Optional[str] = None, level: Optional[str] = None, limit: int = 100) -> list[dict]:
        db = await get_connection()
        query = 'SELECT * FROM logs WHERE 1=1'
        params = []
        if service:
            query += ' AND service = ?'
            params.append(service)
        if level:
            query += ' AND level = ?'
            params.append(level)
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            results = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                row_dict['metadata'] = json.loads(row_dict['metadata']) if row_dict['metadata'] else {}
                results.append(row_dict)
            return results

    async def get_metrics_timeseries(self, service: str, metric_name: str, minutes: int = 60) -> list[dict]:
        db = await get_connection()
        query = '''
            SELECT timestamp, value FROM metrics
            WHERE service = ? AND metric_name = ? AND datetime(timestamp) >= datetime('now', ?)
            ORDER BY timestamp ASC
        '''
        params = (service, metric_name, f'-{minutes} minutes')
        
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [{'timestamp': row[0], 'value': row[1]} for row in rows]

    async def get_recent_incidents(self, limit: int = 20, severity: Optional[str] = None) -> list[dict]:
        db = await get_connection()
        query = 'SELECT * FROM incidents WHERE 1=1'
        params = []
        if severity:
            query += ' AND severity = ?'
            params.append(severity)
        query += ' ORDER BY detected_at DESC LIMIT ?'
        params.append(limit)
        
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            results = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                row_dict['affected_services'] = json.loads(row_dict['affected_services']) if row_dict['affected_services'] else []
                row_dict['evidence'] = json.loads(row_dict['evidence']) if row_dict['evidence'] else []
                row_dict['recommended_actions'] = json.loads(row_dict['recommended_actions']) if row_dict['recommended_actions'] else []
                results.append(row_dict)
            return results

    async def get_incident_by_id(self, incident_id: str) -> Optional[dict]:
        db = await get_connection()
        query = 'SELECT * FROM incidents WHERE id = ?'
        async with db.execute(query, (incident_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            columns = [col[0] for col in cursor.description]
            row_dict = dict(zip(columns, row))
            row_dict['affected_services'] = json.loads(row_dict['affected_services']) if row_dict['affected_services'] else []
            row_dict['evidence'] = json.loads(row_dict['evidence']) if row_dict['evidence'] else []
            row_dict['recommended_actions'] = json.loads(row_dict['recommended_actions']) if row_dict['recommended_actions'] else []
            return row_dict

    async def get_active_incidents(self) -> list[dict]:
        db = await get_connection()
        query = 'SELECT * FROM incidents WHERE status = ? ORDER BY detected_at DESC'
        async with db.execute(query, (IncidentStatus.ACTIVE.value,)) as cursor:
            rows = await cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            results = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                row_dict['affected_services'] = json.loads(row_dict['affected_services']) if row_dict['affected_services'] else []
                row_dict['evidence'] = json.loads(row_dict['evidence']) if row_dict['evidence'] else []
                row_dict['recommended_actions'] = json.loads(row_dict['recommended_actions']) if row_dict['recommended_actions'] else []
                results.append(row_dict)
            return results

    async def get_error_distribution(self, minutes: int = 60) -> list[dict]:
        db = await get_connection()
        query = '''
            SELECT service, COUNT(*) as count 
            FROM logs 
            WHERE level IN ('ERROR', 'CRITICAL') AND datetime(timestamp) >= datetime('now', ?)
            GROUP BY service
            ORDER BY count DESC
        '''
        async with db.execute(query, (f'-{minutes} minutes',)) as cursor:
            rows = await cursor.fetchall()
            total = sum([row[1] for row in rows])
            results = []
            for row in rows:
                service, count = row
                results.append({
                    'service': service,
                    'count': count,
                    'percentage': (count / total * 100) if total > 0 else 0,
                    'top_errors': []
                })
            return results
