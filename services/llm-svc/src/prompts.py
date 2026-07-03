"""Prompt-Templates für die LLM-gesteuerte UC-Panel-Analyse.

Jeder UC hat ein eigenes deutsches Prompt-Template, das die Panel-Daten
als Kontext erhält und eine differenzierte Analyse in 2-3 Absätzen anfordert.

Platzhalter:
  {technology} — Technologie-Suchbegriff
  {data}       — Serialisierte Panel-Daten (JSON)
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Deutsche Prompt-Templates für alle 12 Use Cases
# ---------------------------------------------------------------------------

UC_PROMPTS: dict[str, str] = {
    # UC1 — Technologie-Landschaft
    "landscape": """Analysiere die folgenden Technologie-Landschaftsdaten für "{technology}":
{data}

Erstelle eine differenzierte Analyse in 2-3 Absätzen basierend auf den konkreten Datenpunkten:

**Aktivitätsprofil:** Wie viele Patente und Projekte wurden gefunden? Wie verhält sich das Verhältnis Patent-zu-Projekt? Nenne die konkreten Zahlen und interpretiere, ob die Technologie eher patent- oder forschungsgetrieben ist.

**Wachstumsdynamik:** Interpretiere die CAGR-Werte für Patente und Projekte. Steigt die Aktivität, stagniert sie oder fällt sie? Nenne die CAGR-Prozentwerte und ordne sie ein (z.B. >10%: starkes Wachstum, <0%: rückläufig).

**Technologische Schwerpunkte:** Welche CPC-Klassen dominieren und was bedeuten sie inhaltlich? Gibt es überraschende Verflechtungen oder Lücken?

Nenne durchgehend konkrete Zahlen und Werte aus den Daten. Antworte auf Deutsch.""",

    # UC2 — Reifegrad-Analyse (S-Kurve)
    "maturity": """Analysiere die S-Kurven-Reifegraddaten für "{technology}":
{data}

Erstelle eine differenzierte Analyse in 2-3 Absätzen basierend auf den konkreten Datenpunkten:

**Aktuelle Reifephase:** In welcher Phase befindet sich die Technologie (Emerging, Growth, Mature, Declining)? Was bedeutet das für Investitions- und Adoptionsentscheidungen? Nenne den konkreten Phase-Wert.

**Modellgüte:** Wie gut passt die S-Kurve (R²-Wert)? Ein R² > 0.85 deutet auf zuverlässige Prognose hin, < 0.6 auf hohes Unsicherheitsniveau. Interpretiere den konkreten Wert und was er für die Aussagekraft bedeutet.

**Prognose und strategische Implikationen:** Basierend auf dem S-Kurven-Verlauf — wann könnte der Wendepunkt (Inflection Point) erreicht werden? Was empfiehlt sich für Akteure: frühe Positionierung oder abwartende Beobachtung?

Nenne durchgehend konkrete Zahlen und Werte aus den Daten. Antworte auf Deutsch.""",

    # UC3 — Wettbewerbsanalyse
    "competitive": """Analysiere die Wettbewerbsdaten für "{technology}":
{data}

Erstelle eine differenzierte Analyse in 2-3 Absätzen basierend auf den konkreten Datenpunkten:

**Marktstruktur:** Interpretiere den HHI-Wert — ist der Markt fragmentiert (<1000), moderat konzentriert (1000-2500) oder hochkonzentriert (>2500)? Nenne den konkreten HHI und erkläre die strategischen Implikationen.

**Akteurs-Landschaft:** Wer sind die Top-Akteure nach Patentanteilen? Wie groß ist der Abstand zwischen dem führenden Akteur und den Verfolgern? Gibt es überraschende Akteure (z.B. Universitäten unter Industrieunternehmen)?

**Wettbewerbsdynamik:** Zeigen die Daten Konsolidierung (steigende Konzentration) oder Fragmentierung (neue Akteure)? Welche Chancen oder Risiken ergeben sich für neue Marktteilnehmer?

Nenne durchgehend konkrete Zahlen, Prozentwerte und Akteursnamen aus den Daten. Antworte auf Deutsch.""",

    # UC4 — Förderungsanalyse
    "funding": """Analysiere die Förderungsdaten für "{technology}":
{data}

Erstelle eine differenzierte Analyse in 2-3 Absätzen basierend auf den konkreten Datenpunkten:

**Fördervolumen und Trend:** Wie hoch ist das gesamte EU-Fördervolumen? Steigt oder sinkt die Förderung über die Zeit? Nenne konkrete Beträge und Zeiträume.

**Förderinstrumente:** Wie verteilen sich RIA (Research & Innovation Actions), IA (Innovation Actions) und CSA (Coordination & Support Actions)? Was sagt die Verteilung über den Reifegrad der Technologie-Förderung aus (RIA-dominiert = frühe Phase, IA-dominiert = Marktnähe)?

**Strategische Ausrichtung:** Welche Horizon-Programme fördern die Technologie am stärksten? Welche thematischen Schwerpunkte zeichnen sich ab und was bedeutet das für die EU-Technologiepolitik?

Nenne durchgehend konkrete Zahlen und Programmnamen aus den Daten. Antworte auf Deutsch.""",

    # UC5 — CPC-Technologiefluss
    "cpc_flow": """Analysiere die CPC-Technologiefluss-Daten für "{technology}":
{data}

Erstelle eine differenzierte Analyse in 2-3 Absätzen basierend auf den konkreten Datenpunkten:

**Stärkste Verflechtungen:** Welche CPC-Klassenpaare haben die höchsten Jaccard-Koeffizienten? Nenne die konkreten Werte und erkläre, was die Ko-Klassifikation technologisch bedeutet (z.B. H04L+G06N = Telekommunikation trifft auf KI).

**Netzwerkstruktur:** Gibt es CPC-Klassen die als Hubs fungieren (viele Verbindungen) vs. isolierte Technologiefelder? Was bedeutet hohe Vernetzung für Technologietransfer-Potenzial?

**Konvergenztrends:** Deuten die Flussmuster auf Technologie-Konvergenz hin? Welche bisher getrennten Felder wachsen zusammen und was sind die Implikationen für interdisziplinäre Innovation?

Nenne durchgehend konkrete Jaccard-Werte und CPC-Klassen aus den Daten. Antworte auf Deutsch.""",

    # UC6 — Geographische Verteilung
    "geographic": """Analysiere die geographischen Verteilungsdaten für "{technology}":
{data}

Erstelle eine differenzierte Analyse in 2-3 Absätzen basierend auf den konkreten Datenpunkten:

**Führende Länder:** Welche Länder dominieren bei Patenten und welche bei Forschungsprojekten? Nenne die Top-3-5 mit konkreten Zahlen oder Anteilen. Gibt es Länder die in Forschung stark sind aber wenig patentieren (oder umgekehrt)?

**Konzentration vs. Diversität:** Wie konzentriert ist die globale Aktivität? Wird die Technologie von wenigen Ländern dominiert oder ist sie breit verteilt? Nenne konkrete Konzentrationskennzahlen.

**Kollaborationsmuster:** Welche Länderpaare kollaborieren am intensivsten? Gibt es überraschende Kooperationsachsen (z.B. EU-Asien-Brücken)? Was bedeutet die geographische Verteilung für die Wettbewerbsposition Europas?

Nenne durchgehend konkrete Länder, Zahlen und Prozentwerte aus den Daten. Antworte auf Deutsch.""",

    # UC7 — Forschungsimpact
    "research_impact": """Analysiere die Forschungsimpact-Daten für "{technology}":
{data}

Erstelle eine differenzierte Analyse in 2-3 Absätzen basierend auf den konkreten Datenpunkten:

**Impact-Kennzahlen:** Wie hoch ist der h-Index für dieses Technologiefeld? Nenne den konkreten Wert und ordne ihn ein (Vergleich: h-Index >50 = etabliertes Großfeld, <10 = Nischengebiet). Wie entwickeln sich die Zitationszahlen über die Zeit?

**Einflussreichste Forschung:** Welche Publikationen oder Autoren stechen durch besonders hohe Zitationszahlen hervor? Was sind deren thematische Schwerpunkte?

**Forschungstrend:** Steigt der Impact (mehr Zitationen, höhere Qualität) oder lässt er nach? Was bedeutet das für die wissenschaftliche Reife des Feldes und die Verbindung zwischen Forschung und Anwendung?

Nenne durchgehend konkrete Zahlen, h-Index-Werte und Zitationszahlen aus den Daten. Antworte auf Deutsch.""",

    # UC8 — Zeitliche Entwicklung
    "temporal": """Analysiere die zeitlichen Entwicklungsdaten für "{technology}":
{data}

Erstelle eine differenzierte Analyse in 2-3 Absätzen basierend auf den konkreten Datenpunkten:

**Akteursdynamik:** Wie hat sich die Anzahl aktiver Akteure über die Zeit verändert? Gibt es Phasen starken Zuwachses oder Abgangs? Wie hoch ist die Persistenzrate (bleiben Akteure langfristig aktiv)?

**Programm-Evolution:** Wie haben sich die Förderprogramme und -volumina über die Jahre entwickelt? Gab es Brüche oder Beschleunigungen durch bestimmte politische Initiativen?

**Technologiebreite:** Wird das Feld breiter (mehr CPC-Klassen, mehr Disziplinen) oder enger (Spezialisierung)? Was bedeutet der zeitliche Verlauf für die Zukunftsaussichten der Technologie?

Nenne durchgehend konkrete Jahreszahlen, Trends und Veränderungsraten aus den Daten. Antworte auf Deutsch.""",

    # UC9 — Technologie-Cluster
    "tech_cluster": """Analysiere die Technologie-Cluster-Daten für "{technology}":
{data}

Erstelle eine differenzierte Analyse in 2-3 Absätzen basierend auf den konkreten Datenpunkten:

**Cluster-Qualität:** Wie viele Cluster wurden identifiziert und wie gut ist die Trennung (Silhouette Score)? Nenne den konkreten Score und interpretiere ihn (>0.5 = gute Trennung, <0.25 = fragwürdig). Was bedeutet das für die technologische Differenzierung?

**Cluster-Charakteristik:** Welche CPC-Klassen prägen die größten Cluster? Handelt es sich um thematisch kohärente Technologiegruppen oder um heterogene Mischungen?

**Innovationspotenzial:** Welche Cluster zeigen Wachstum (steigende Patentaktivität) und welche stagnieren? Gibt es kleine aber schnell wachsende Cluster die auf emerging sub-fields hindeuten?

Nenne durchgehend konkrete Cluster-IDs, Scores und CPC-Klassen aus den Daten. Antworte auf Deutsch.""",

    # UC10 — Wissenschaftsdisziplinen (EuroSciVoc)
    "euroscivoc": """Analysiere die EuroSciVoc-Wissenschaftsdisziplinen-Daten für "{technology}":
{data}

Erstelle eine differenzierte Analyse in 2-3 Absätzen basierend auf den konkreten Datenpunkten:

**Disziplinäre Schwerpunkte:** Welche Wissenschaftsdisziplinen dominieren und mit welchem Anteil? Nenne die Top-5 mit konkreten Prozentwerten. Entspricht die Verteilung den Erwartungen oder gibt es Überraschungen?

**Interdisziplinarität:** Wie hoch ist der Shannon-Diversitätsindex? Nenne den konkreten Wert und interpretiere ihn (hoch = stark interdisziplinär, niedrig = disziplinär fokussiert). Was bedeutet das für das Innovationspotenzial?

**Aufkommende Disziplinen:** Gibt es Disziplinen die erst kürzlich an Bedeutung gewonnen haben? Welche Schnittstellen zwischen Disziplinen könnten besonders innovationsträchtig sein?

Nenne durchgehend konkrete Disziplin-Namen, Anteile und Index-Werte aus den Daten. Antworte auf Deutsch.""",

    # UC11 — Akteurs-Typverteilung
    "actor_type": """Analysiere die Akteurs-Typverteilungsdaten für "{technology}":
{data}

Erstelle eine differenzierte Analyse in 2-3 Absätzen basierend auf den konkreten Datenpunkten:

**Akteursverteilung:** Wie verteilen sich HES (Hochschulen), PRC (Unternehmen), REC (Forschungseinrichtungen) und andere Akteurstypen? Nenne die konkreten Anteile. Welcher Typ dominiert und was sagt das über den Reifegrad der Technologie?

**Forschung vs. Anwendung:** Überwiegt Grundlagenforschung (hoher HES/REC-Anteil) oder industrielle Anwendung (hoher PRC-Anteil)? Wie ist das Verhältnis und was bedeutet es für den Technologietransfer?

**Strategische Implikationen:** Ist die Akteurslandschaft ausgewogen oder gibt es Schieflagen? Was empfiehlt sich für die Förderpolitik — mehr Industriebeteiligung fördern oder akademische Freiheit stärken?

Nenne durchgehend konkrete Akteurszahlen, Typen und Anteile aus den Daten. Antworte auf Deutsch.""",

    # UC12 — Erteilungsquoten (Patent Grant)
    "patent_grant": """Analysiere die Patent-Erteilungsdaten für "{technology}":
{data}

Erstelle eine differenzierte Analyse in 2-3 Absätzen basierend auf den konkreten Datenpunkten:

**Erteilungsquote:** Wie hoch ist die Grant Rate und wie verhält sie sich zum typischen EPO-Durchschnitt (~50-60%)? Nenne den konkreten Prozentwert. Eine hohe Rate deutet auf etablierte Patentqualität hin, eine niedrige auf ein schwieriges IP-Umfeld.

**Zeitlicher Verlauf:** Wie entwickeln sich Anmeldungen und Erteilungen über die Jahre? Gibt es eine zunehmende oder abnehmende Lücke zwischen Anmeldungen und Grants? Nenne konkrete Jahreszahlen und Trends.

**Innovationsreife:** Was sagen die Erteilungsmuster über die technologische Reife aus? Eine stabile hohe Grant Rate bei steigenden Anmeldungen signalisiert ein gesundes Innovationsfeld. Welche Handlungsempfehlung ergibt sich?

Nenne durchgehend konkrete Quoten, Zahlen und Zeiträume aus den Daten. Antworte auf Deutsch.""",

    # UC-C — Publikationsanalyse (Publication Analytics)
    "publication": """Analysiere die Publikationsdaten aus CORDIS-Projekten für "{technology}":
{data}

Erstelle eine differenzierte Analyse in 2-3 Absätzen basierend auf den konkreten Datenpunkten:

**Publikationsaufkommen:** Wie viele Publikationen wurden gefunden und wie verteilen sie sich zeitlich? Nenne die konkrete Gesamtzahl und markante Jahre (z.B. Aktivitätsspitzen). Wachsen die Publikationszahlen oder stagnieren sie?

**Publikationstypen und Open Access:** Wie ist die Verteilung zwischen Journal Articles, Conference Proceedings, Book Chapters und anderen Typen? Wie hoch ist der Open-Access-Anteil und was sagt das über die Zugänglichkeit der Forschung in diesem Feld aus?

**Führende Journals und thematische Schwerpunkte:** Welche Journals oder Venues dominieren? Gibt es einen klaren thematischen Fokus oder eine breite Streuung über viele Publikationsorgane? Was bedeutet die Verteilung für die wissenschaftliche Reife und das Kommunikationsverhalten im Feld?

Nenne durchgehend konkrete Zahlen, Anteile und Journal-Namen aus den Daten. Antworte auf Deutsch.""",
}

# ---------------------------------------------------------------------------
# System-Prompt für alle UC-Analysen
# ---------------------------------------------------------------------------

SYSTEM_PROMPT: str = """Du bist ein Experte für Technologie-Intelligence und analysierst \
strukturierte Daten aus Patent-, Förderungs- und Publikationsdatenbanken. \
Deine Aufgabe ist es, die bereitgestellten Daten differenziert zu interpretieren \
und strategische Erkenntnisse abzuleiten.

Richtlinien:
- Antworte in 2-3 strukturierten Absätzen mit konkreten Datenpunkten
- Nenne immer spezifische Zahlen, Prozentwerte und Kennzahlen aus den Daten
- Interpretiere die Werte: Was bedeuten sie im Kontext, was ist hoch/niedrig?
- Verwende Fachbegriffe und erkläre sie bei Bedarf
- Stütze dich ausschließlich auf die bereitgestellten Daten
- Leite strategische Implikationen und Handlungsempfehlungen ab
- Formatiere mit **Fettdruck** für Schlüsselerkenntnisse"""


# ---------------------------------------------------------------------------
# RAG Context Prompt Template — für AnalyzePanelWithContext
# ---------------------------------------------------------------------------

RAG_CONTEXT_TEMPLATE = """
Relevante Dokumente aus der Wissensbasis:

{context_block}

---
Panel-Daten (aggregiert):
{panel_data}

Analysiere {use_case_key} für die Technologie "{technology}".
Beziehe die oben genannten Dokumente in deine Analyse ein und verweise auf konkrete Quellen.
"""

# ---------------------------------------------------------------------------
# Chat Prompt Templates — für interaktiven Chat mit RAG-Kontext
# ---------------------------------------------------------------------------

CHAT_SYSTEM_PROMPT = """Du bist ein Technologie-Experte für "{technology}" im TI-Radar System.
Du antwortest ausführlich und faktenbasiert auf Basis der bereitgestellten Quellen und Analyse-Daten.

Richtlinien:
- Antworte in mehreren Absätzen, nicht nur in einem Satz
- Erkläre Kennzahlen verständlich: Was bedeuten HHI, CAGR, R², Shannon-Index konkret?
- Nenne spezifische Zahlen und Werte aus den bereitgestellten Daten
- Ordne die Werte ein: Ist ein Wert hoch oder niedrig? Was bedeutet das?
- Leite strategische Schlussfolgerungen ab
- Zitiere Quellen mit [1], [2], etc. am Ende relevanter Aussagen
- Wenn du etwas nicht aus den Quellen oder Daten beantworten kannst, sage das ehrlich
- Verwende **Fettdruck** für Schlüsselerkenntnisse

Antworte auf {language}."""

CHAT_USER_TEMPLATE = """
{panel_block}
Quellen:
{sources_block}

Frage: {user_message}
"""


def format_context_block(documents: list) -> str:  # type: ignore[type-arg]
    """Formatiert RetrievedDocuments als nummerierter Kontext-Block.

    Args:
        documents: Liste von RetrievedDocument-Objekten (Protobuf oder Mock).

    Returns:
        Nummerierter Text-Block mit Quelle, Titel und Snippet.
    """
    lines: list[str] = []
    for i, doc in enumerate(documents, 1):
        source_label = getattr(doc, "source", "unknown")
        title = getattr(doc, "title", "")
        snippet = getattr(doc, "text_snippet", "")
        lines.append(f"[{i}] ({source_label}) {title}: {snippet}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Panel-Kontext Formatierung — für analyseberücksichtigenden Chat
# ---------------------------------------------------------------------------

_PANEL_LABELS: dict[str, str] = {
    "landscape": "Technologie-Landschaft (UC1)",
    "maturity": "Reifegrad / S-Kurve (UC2)",
    "competitive": "Wettbewerbsanalyse (UC3)",
    "funding": "Förderungsanalyse (UC4)",
    "cpc_flow": "CPC-Technologiefluss (UC5)",
    "geographic": "Geographische Verteilung (UC6)",
    "research_impact": "Forschungsimpact (UC7)",
    "temporal": "Zeitliche Entwicklung (UC8)",
    "tech_cluster": "Technologie-Cluster (UC9)",
    "euroscivoc": "Wissenschaftsdisziplinen (UC10)",
    "actor_type": "Akteurs-Typverteilung (UC11)",
    "patent_grant": "Patent-Erteilungsquoten (UC12)",
    "publication": "Publikationsanalyse (UC-C)",
}


def format_panel_context(panel_context_json: str) -> str:
    """Formatiert Panel-Kontext-JSON als lesbaren Kontext-Block.

    Args:
        panel_context_json: JSON-String mit Panel-Daten aus dem Frontend.
            Erwartet: {"active_panel": "maturity", "data": {...}}
            Oder: {"panels": {"landscape": {...}, "maturity": {...}}}

    Returns:
        Formatierter Text-Block oder leerer String wenn kein Kontext.
    """
    if not panel_context_json or panel_context_json.strip() in ("", "{}"):
        return ""

    try:
        import json
        ctx = json.loads(panel_context_json)
    except (json.JSONDecodeError, TypeError):
        return f"Analyse-Daten:\n{panel_context_json[:8000]}"

    if not ctx:
        return ""

    lines: list[str] = []

    # Format 1: Single active panel
    active = ctx.get("active_panel", "")
    if active and "data" in ctx:
        label = _PANEL_LABELS.get(active, active)
        lines.append(f"Aktuell angezeigte Analyse: {label}")
        data_str = json.dumps(ctx["data"], ensure_ascii=False, indent=2)
        if len(data_str) > 8000:
            data_str = data_str[:8000] + "\n... [gekürzt]"
        lines.append(data_str)
        return "\n".join(lines)

    # Format 2: Multiple panels summary
    panels = ctx.get("panels", ctx)
    if isinstance(panels, dict):
        for key, val in panels.items():
            if key in _PANEL_LABELS and val:
                label = _PANEL_LABELS[key]
                summary = json.dumps(val, ensure_ascii=False)
                if len(summary) > 1000:
                    summary = summary[:1000] + "..."
                lines.append(f"- {label}: {summary}")
        return "\n".join(lines) if lines else ""

    return ""
