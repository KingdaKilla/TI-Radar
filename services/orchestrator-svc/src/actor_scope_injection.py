"""Helper zur Injection des Akteurs-Scope-Labels (Bug CRIT-3 / AP3).

UC8 (temporal), UC9 (tech_cluster) und UC11 (actor_type) zählen Akteure
in drei verschiedenen Scopes. Damit das Frontend dem Nutzer klarmachen
kann, welche Population er sieht, injiziert der Orchestrator nach der
Proto->Dict-Konvertierung das kanonische Label.

Warum ein eigenes Modul? ``router_radar`` zieht ganze
FastAPI/Prometheus-Abhängigkeitsketten nach. Die Injection-Logik
selbst ist aber rein datengebunden und soll in Unit-Tests ohne
HTTP-Dependencies laufbar sein. Deshalb separates Modul.
"""

from __future__ import annotations

from typing import Any

from shared.domain.actor_definitions import ActorScope, canonical_actor_label

# UC-Name -> kanonischer Scope. Nicht gelistete UCs bleiben unverändert.
UC_ACTOR_SCOPE: dict[str, ActorScope] = {
    "temporal": ActorScope.ACTIVE_IN_WINDOW,
    "tech_cluster": ActorScope.CLUSTER_MEMBER,
    "actor_type": ActorScope.CLASSIFIED,
}


def inject_actor_scope_label(uc_name: str, panel_data: dict[str, Any]) -> None:
    """Ergänzt ``panel_data`` um ``actor_scope`` und ``actor_scope_label``.

    Args:
        uc_name: UC-Schlüssel wie ``"temporal"``, ``"tech_cluster"`` oder
                 ``"actor_type"``. Andere Werte sind No-Ops.
        panel_data: Dict-Response, wird in-place mutiert.

    Regeln:
        - UCs außerhalb von ``UC_ACTOR_SCOPE`` bleiben unverändert.
        - Bereits gesetzte ``actor_scope``-Werte werden *nicht* über-
          schrieben (``setdefault``).
    """
    scope = UC_ACTOR_SCOPE.get(uc_name)
    if scope is None:
        return
    panel_data.setdefault("actor_scope", scope.value)
    panel_data.setdefault("actor_scope_label", canonical_actor_label(scope))


__all__ = [
    "UC_ACTOR_SCOPE",
    "inject_actor_scope_label",
]
