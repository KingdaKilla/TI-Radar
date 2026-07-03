"""Orchestrator Service — API-Gateway für die TI-Radar v3 Plattform.

Empfängt REST-Requests vom Frontend und verteilt sie per gRPC
an 13 UC-Microservices. Implementiert Graceful Degradation, Per-UC-Timeouts
und Prometheus-Metriken.
"""

__version__ = "3.0.0"
