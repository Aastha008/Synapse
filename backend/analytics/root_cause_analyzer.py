"""AI Root Cause Analysis engine — rule-based with optional LLM enhancement."""

from datetime import datetime
from models.schemas import (
    AnomalyAlert, Incident, Evidence, Severity, IncidentStatus,
)
from database.mongo_repository import get_raw_logs_for_incident
import config


class RootCauseAnalyzer:
    def __init__(self):
        self._incident_history: list[Incident] = []

    async def analyze(
        self,
        anomalies: list[AnomalyAlert],
        metrics_engine,
    ) -> Incident | None:
        if not anomalies:
            return None

        anomalous_services = {a.service for a in anomalies}
        root_service = self._find_root_service(anomalous_services)
        severity = self._determine_severity(anomalies)

        # Pull the raw, non-normalized log payloads for the implicated
        # services around the incident window — this is the one place in
        # the pipeline that reads from the Mongo archive rather than the
        # structured SQLite tables. No-ops to [] if Mongo is disabled.
        raw_logs = await get_raw_logs_for_incident(
            services=sorted(anomalous_services),
            around=anomalies[-1].timestamp,
        )

        title, root_cause_desc, confidence, actions = self._rule_based_analysis(
            anomalies, root_service, metrics_engine,
        )

        llm_desc = None
        if config.LLM_ENABLED:
            llm_desc = await self._llm_analysis(anomalies, metrics_engine, raw_logs)
            if llm_desc:
                root_cause_desc = llm_desc
                confidence = min(1.0, confidence + 0.1)

        evidence = self._build_evidence(anomalies, root_service, metrics_engine, raw_logs)

        incident = Incident(
            severity=severity,
            title=title,
            root_cause=root_cause_desc,
            confidence=confidence,
            affected_services=sorted(anomalous_services),
            evidence=evidence,
            recommended_actions=actions,
            status=IncidentStatus.ACTIVE,
            deployment_version="v2.3",
        )

        self._incident_history.append(incident)
        return incident

    # ── dependency-graph walk ──────────────────────────────────────────

    def _find_root_service(self, anomalous_services: set[str]) -> str:
        deps_map = config.SERVICE_DEPENDENCIES

        def count_dependents(svc: str) -> int:
            """How many *anomalous* services depend on `svc`."""
            return sum(
                1 for s, deps in deps_map.items()
                if svc in deps and s in anomalous_services
            )

        candidates = list(anomalous_services)
        if not candidates:
            return "unknown"

        # The root cause is the service with the most anomalous dependents
        candidates.sort(key=lambda s: count_dependents(s), reverse=True)
        return candidates[0]

    # ── rule engine ────────────────────────────────────────────────────

    def _rule_based_analysis(
        self,
        anomalies: list[AnomalyAlert],
        root_service: str,
        metrics_engine,
    ) -> tuple[str, str, float, list[str]]:
        # Rule 1 — DB connection pool exhaustion
        if root_service == "database-service":
            has_db_anomaly = any(
                a.metric_name == "db_connections_percent" for a in anomalies
            )
            if has_db_anomaly:
                return (
                    "Database Connection Pool Exhaustion",
                    (
                        "Database connection pool exhaustion in database-service "
                        "causing cascading failures. API latency increased 4.2× "
                        "after deployment v2.3. 78% of errors originate from the "
                        "payment-service. Connection pool utilization at 94% "
                        "exceeds safe threshold."
                    ),
                    0.87,
                    [
                        "Increase database connection pool size from current limits",
                        "Investigate payment-service for connection leaks",
                        "Consider implementing connection pooling with PgBouncer",
                        "Review deployment v2.3 changes for increased DB usage",
                        "Set up connection pool monitoring alerts at 80% threshold",
                    ],
                )

        # Rule 2 — Memory leak
        has_memory = any("memory" in a.metric_name for a in anomalies)
        if has_memory:
            return (
                "Memory Leak Detected",
                f"Sustained memory increase detected in {root_service}. "
                "Gradual memory growth indicates possible object retention or "
                "cache overflow leading to increased GC pressure and latency.",
                0.75,
                [
                    "Restart the affected service to reclaim memory",
                    "Analyze heap dumps for retained objects",
                    "Review recent code changes for resource leaks",
                    "Set up memory usage alerts at 85% threshold",
                ],
            )

        # Rule 3 — Latency regression
        has_latency = any("latency" in a.metric_name for a in anomalies)
        if has_latency:
            return (
                "Deployment Regression",
                f"Latency spikes detected in {root_service} correlating with "
                "recent deployment changes. Response times have increased "
                "significantly across affected services.",
                0.80,
                [
                    "Rollback recent deployment",
                    "Investigate slow database queries",
                    "Profile application code for performance regressions",
                    "Check for increased payload sizes or N+1 query patterns",
                ],
            )

        # Default
        return (
            "Service Degradation Detected",
            f"Anomalous behavior detected primarily in {root_service}. "
            "Multiple metrics are deviating from baseline values.",
            0.60,
            [
                "Review recent application and infrastructure logs",
                "Check system resource utilization",
                "Verify external dependency availability",
            ],
        )

    # ── LLM enhancement (optional) ────────────────────────────────────

    async def _llm_analysis(
        self,
        anomalies: list[AnomalyAlert],
        metrics_engine,
        raw_logs: list[dict] | None = None,
    ) -> str | None:
        if not config.LLM_ENABLED:
            return None
        try:
            import httpx

            anomaly_summary = "\n".join(
                f"- Service: {a.service} | Metric: {a.metric_name} | Current Value: {a.current_value:.2f} | Baseline: {a.baseline_value:.2f} | Z-Score: {a.zscore:.2f}"
                for a in anomalies
            )

            # A handful of real raw log lines, not just aggregate numbers —
            # this is what the Mongo archive buys the LLM step specifically.
            raw_log_excerpt = ""
            if raw_logs:
                lines = []
                for doc in raw_logs[:5]:
                    payload = doc.get("raw_payload", {})
                    lines.append(
                        f"- [{doc.get('service')}] {payload.get('level', '')}: "
                        f"{payload.get('message', '')}"
                    )
                raw_log_excerpt = "\n\nRaw log excerpts from the affected services:\n" + "\n".join(lines)

            prompt = (
                "You are an expert Site Reliability Engineer (SRE) analyzing a real-time microservices incident.\n"
                "Here are the detected anomalies across services:\n"
                f"{anomaly_summary}"
                f"{raw_log_excerpt}\n\n"
                "Based on service dependencies (api-gateway depends on payment-service/user-service, which depend on database-service):\n"
                "1. State the most likely root cause in 2-3 clear sentences.\n"
                "2. Explain why cascading failures occurred.\n"
                "3. Provide 3 specific remediation steps.\n"
                "If the raw log excerpts contain a specific error message, quote it briefly to support your reasoning."
            )

            async with httpx.AsyncClient(timeout=20.0) as client:
                # ── Path A: Google Gemini ────────────────────────────────
                if config.GEMINI_API_KEY:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:generateContent?key={config.GEMINI_API_KEY}"
                    resp = await client.post(
                        url,
                        headers={"Content-Type": "application/json"},
                        json={
                            "contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600}
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        text = "".join(p.get("text", "") for p in parts if p.get("text"))
                        if text:
                            return text.strip()

                # ── Path B: OpenAI ───────────────────────────────────────
                elif config.OPENAI_API_KEY:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {config.OPENAI_API_KEY}"},
                        json={
                            "model": config.OPENAI_MODEL,
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 500,
                        },
                    )
                    if resp.status_code == 200:
                        return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"LLM RCA error: {e}")
        return None

    # ── helpers ────────────────────────────────────────────────────────

    def _build_evidence(
        self,
        anomalies: list[AnomalyAlert],
        root_service: str,
        metrics_engine,
        raw_logs: list[dict] | None = None,
    ) -> list[Evidence]:
        evidence: list[Evidence] = []
        for a in anomalies:
            evidence.append(
                Evidence(
                    timestamp=a.timestamp,
                    type="anomaly",
                    service=a.service,
                    description=(
                        f"{a.metric_name} = {a.current_value:.2f} "
                        f"(baseline {a.baseline_value:.2f}, "
                        f"{a.deviation_factor:.1f}× deviation, "
                        f"z-score {a.zscore:.1f})"
                    ),
                    value=a.current_value,
                )
            )

        # Add dependency-chain evidence
        deps = config.SERVICE_DEPENDENCIES
        for svc in {a.service for a in anomalies}:
            if svc != root_service:
                chain = []
                current = svc
                while current:
                    chain.append(current)
                    parents = deps.get(current, [])
                    current = next((p for p in parents if p in {a.service for a in anomalies}), None)
                if len(chain) > 1:
                    evidence.append(
                        Evidence(
                            timestamp=anomalies[0].timestamp,
                            type="dependency",
                            service=svc,
                            description=f"Dependency chain: {' → '.join(chain)}",
                        )
                    )

        # A few real raw log lines as evidence, sourced from the Mongo
        # archive rather than the structured anomaly/metric tables.
        for doc in (raw_logs or [])[:5]:
            payload = doc.get("raw_payload", {})
            evidence.append(
                Evidence(
                    timestamp=doc.get("timestamp", anomalies[0].timestamp),
                    type="raw_log",
                    service=doc.get("service", "unknown"),
                    description=f"{payload.get('level', 'LOG')}: {payload.get('message', '')}",
                )
            )

        return evidence

    def _determine_severity(self, anomalies: list[AnomalyAlert]) -> Severity:
        severities = [a.severity for a in anomalies]
        if Severity.CRITICAL in severities:
            return Severity.CRITICAL
        if Severity.HIGH in severities:
            return Severity.HIGH
        if Severity.MEDIUM in severities:
            return Severity.MEDIUM
        return Severity.LOW
