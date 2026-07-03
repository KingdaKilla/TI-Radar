"""LandscapeRepository — PostgreSQL-Datenbankzugriff für UC1.

Migriert von SQLite (aiosqlite + FTS5) zu PostgreSQL (asyncpg + tsvector).
Nutzt den asyncpg Connection Pool für hochperformanten async Zugriff.

Zentrale Migrationsänderungen gegenüber v1.0:
- FTS5 MATCH -> tsvector @@ plainto_tsquery('english', ...)
- SUBSTR(publication_date, 1, 4) -> publication_year (Partition-Key)
- WHERE country IN ('AT','BE',...) -> WHERE applicant_countries && '{AT,BE,...}'::text[]
- ? Placeholder -> $1, $2 (asyncpg Dollar-Notation)
- aiosqlite.connect() -> pool.acquire() (Connection Pool)
- Materialized Views wo verfügbar (statt Raw-Table-Queries)

Datenbankschema (PostgreSQL):
- patent_schema.patents: 154.8M Zeilen, partitioniert nach publication_year
  Spalten: id, publication_number, country, title, publication_date,
  publication_year, family_id, applicant_countries (text[]), cpc_codes (text[]),
  search_vector (tsvector, GIN-indexiert)
- patent_schema.patent_cpc: 237M Zeilen, co-partitioniert nach pub_year
  Spalten: patent_id, cpc_code (VARCHAR(8)), pub_year
- patent_schema.cpc_descriptions: ~670 Einträge (statische Referenztabelle)
  Spalten: code, section, class_code, description_en, description_de
- cordis_schema.projects: 80.5K Zeilen
  Spalten: id, framework, acronym, title, objective, start_date, end_date,
  total_cost, ec_max_contribution, funding_scheme, search_vector
- cordis_schema.organizations: 438K Zeilen
  Spalten: id, project_id, name, country, city, role, ec_contribution
"""

from __future__ import annotations

from typing import Any

import asyncpg
import structlog

from shared.domain.patent_definitions import PatentScope, canonical_patent_label
from shared.domain.result_types import CountryCount, CpcCount, FundingYear, YearCount

logger = structlog.get_logger(__name__)

# Bug CRIT-4: Der Header (UC1) zählt Patente im Scope
# ``PatentScope.ALL_PATENTS`` — d.h. OHNE Kind-Code-Filter. UC12 zählt
# dagegen in den Scopes ``APPLICATIONS_ONLY`` (A*) bzw. ``GRANTS_ONLY`` (B*).
# Die Plausibilitätsregel ist:
#     ALL_PATENTS >= APPLICATIONS_ONLY + GRANTS_ONLY
# (Rest = Kind-Codes wie U, D0 oder leer.)
_HEADER_PATENT_SCOPE: PatentScope = PatentScope.ALL_PATENTS
_HEADER_PATENT_LABEL: str = canonical_patent_label(_HEADER_PATENT_SCOPE)

# EU/EEA-Ländercodes für european_only-Filter
EU_EEA_COUNTRIES: frozenset[str] = frozenset({
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
    # EEA (nicht EU)
    "IS", "LI", "NO",
    # Assoziierte (CH, UK)
    "CH", "GB",
})


class LandscapeRepository:
    """Async PostgreSQL-Zugriff für UC1 Landscape-Analysen.

    Alle Methoden verwenden den übergebenen asyncpg Connection Pool.
    Queries nutzen PostgreSQL-spezifische Syntax:
    - tsvector @@ plainto_tsquery für Volltextsuche
    - $1, $2 für Parameter-Binding (SQL-Injection-Schutz)
    - text[] mit && und @> für Array-Operationen
    - Materialized Views für voraggregierte Daten

    Die Klasse implementiert das Repository-Pattern und kapselt alle
    SQL-Abfragen. Der Service-Layer (LandscapeServicer) ruft die
    Methoden parallel via asyncio.gather auf.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        """Repository initialisieren.

        Args:
            pool: asyncpg Connection Pool, erstellt in server.py.
        """
        self._pool = pool

    # -----------------------------------------------------------------------
    # Patent-Abfragen
    # -----------------------------------------------------------------------

    async def count_patents_by_year(
        self,
        technology: str,
        *,
        start_year: int | None = None,
        end_year: int | None = None,
        european_only: bool = False,
    ) -> list[YearCount]:
        """Patentanzahl pro Jahr für eine Technologie.

        Scope: ``PatentScope.ALL_PATENTS`` — d.h. *alle* Patente werden
        gezählt, unabhängig vom EPO-Kind-Code (A*, B*, U, D0, leer).
        Dies ist die Header-Semantik aus UC1 (``total_patents``) und
        muss konsistent zur Plausibilitätsregel
        ``ALL_PATENTS >= APPLICATIONS_ONLY + GRANTS_ONLY`` bleiben
        (siehe Bug CRIT-4, ``shared.domain.patent_definitions``).

        Nutzt tsvector-Volltextsuche auf patent_schema.patents.search_vector.
        Partition Pruning über publication_year (WHERE-Klausel).

        Args:
            technology: Suchbegriff für Volltextsuche (z.B. 'quantum computing').
            start_year: Erstes Jahr im Zeitraum (inklusiv). None = unbeschränkt.
            end_year: Letztes Jahr im Zeitraum (inklusiv). None = unbeschränkt.
            european_only: Nur Patente mit EU/EEA-Anmeldern berücksichtigen.

        Returns:
            Liste von Dicts mit Schlüssel 'year' (int) und 'count' (int),
            sortiert aufsteigend nach Jahr.
        """
        conditions = ["p.search_vector @@ plainto_tsquery('english', $1)"]
        params: list[Any] = [technology]
        idx = 2  # Nächster Parameter-Index

        if start_year is not None:
            conditions.append(f"p.publication_year >= ${idx}")
            params.append(start_year)
            idx += 1

        if end_year is not None:
            conditions.append(f"p.publication_year <= ${idx}")
            params.append(end_year)
            idx += 1

        if european_only:
            conditions.append(
                f"p.applicant_countries && ${idx}::text[]"
            )
            params.append(list(EU_EEA_COUNTRIES))
            idx += 1

        where = " AND ".join(conditions)

        sql = f"""
            SELECT p.publication_year AS year,
                   COUNT(*) AS count
            FROM patent_schema.patents p
            WHERE {where}
              AND p.publication_year IS NOT NULL
            GROUP BY p.publication_year
            ORDER BY p.publication_year
        """

        logger.debug(
            "query_patents_by_year",
            technology=technology,
            start_year=start_year,
            end_year=end_year,
            european_only=european_only,
        )

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [YearCount(year=row["year"], count=row["count"]) for row in rows]

    async def count_patents_by_country(
        self,
        technology: str,
        *,
        start_year: int | None = None,
        end_year: int | None = None,
        european_only: bool = False,
        limit: int = 20,
    ) -> list[CountryCount]:
        """Patentanzahl pro Anmelder-Land für eine Technologie.

        Nutzt LATERAL unnest() auf applicant_countries (text[]-Array).
        Ersetzt die CSV-Parsing-Logik aus v1.0 (WHERE LIKE '%XX%').

        Args:
            technology: Suchbegriff für Volltextsuche.
            start_year: Erstes Jahr (inklusiv).
            end_year: Letztes Jahr (inklusiv).
            european_only: Nur EU/EEA-Länder zählen.
            limit: Maximale Anzahl Länder im Ergebnis (Top-N).

        Returns:
            Liste von Dicts mit 'country' (str, ISO-2) und 'count' (int),
            absteigend sortiert nach count.
        """
        conditions = ["p.search_vector @@ plainto_tsquery('english', $1)"]
        params: list[Any] = [technology]
        idx = 2

        if start_year is not None:
            conditions.append(f"p.publication_year >= ${idx}")
            params.append(start_year)
            idx += 1

        if end_year is not None:
            conditions.append(f"p.publication_year <= ${idx}")
            params.append(end_year)
            idx += 1

        # EU-Filter: nur Patente mit mindestens einem EU-Anmelder
        if european_only:
            conditions.append(f"p.applicant_countries && ${idx}::text[]")
            params.append(list(EU_EEA_COUNTRIES))
            idx += 1

        where = " AND ".join(conditions)

        # EU-Filter auf das ungenestete Land (nur EU-Länder zählen)
        country_filter = ""
        if european_only:
            country_filter = f"AND c.country_code = ANY(${idx}::text[])"
            params.append(list(EU_EEA_COUNTRIES))
            idx += 1

        params.append(limit)
        limit_idx = idx

        sql = f"""
            SELECT c.country_code AS country,
                   COUNT(*) AS count
            FROM patent_schema.patents p,
                 LATERAL unnest(p.applicant_countries) AS c(country_code)
            WHERE {where}
              AND p.applicant_countries IS NOT NULL
              AND array_length(p.applicant_countries, 1) > 0
              {country_filter}
            GROUP BY c.country_code
            ORDER BY count DESC
            LIMIT ${limit_idx}
        """

        logger.debug(
            "query_patents_by_country",
            technology=technology,
            european_only=european_only,
            limit=limit,
        )

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [CountryCount(country=row["country"], count=row["count"]) for row in rows]

    async def top_cpc_codes(
        self,
        technology: str,
        *,
        start_year: int | None = None,
        end_year: int | None = None,
        limit: int = 15,
    ) -> list[CpcCount]:
        """Top-CPC-Codes für eine Technologie.

        Nutzt die normalisierte patent_cpc-Tabelle (237M Zeilen) und joined
        mit cpc_descriptions (~670 Einträge) für menschenlesbare Beschreibungen.
        Co-Partition patent_cpc.pub_year = patents.publication_year ermöglicht
        effizientes Partition Pruning.

        Args:
            technology: Suchbegriff für Volltextsuche.
            start_year: Erstes Jahr (inklusiv).
            end_year: Letztes Jahr (inklusiv).
            limit: Maximale Anzahl CPC-Codes (Top-N).

        Returns:
            Liste von Dicts mit 'code' (str, z.B. 'H04W'),
            'description' (str, englisch) und 'count' (int),
            absteigend sortiert nach count.
        """
        conditions = ["p.search_vector @@ plainto_tsquery('english', $1)"]
        params: list[Any] = [technology]
        idx = 2

        if start_year is not None:
            conditions.append(f"p.publication_year >= ${idx}")
            params.append(start_year)
            idx += 1

        if end_year is not None:
            conditions.append(f"p.publication_year <= ${idx}")
            params.append(end_year)
            idx += 1

        where = " AND ".join(conditions)
        params.append(limit)
        limit_idx = idx

        # Fallback: wenn patent_cpc leer ist, direkt aus patents.cpc_codes lesen.
        # JOIN auf cpc_descriptions mit längstem Präfix-Match (exact -> kürzer).
        sql = f"""
            SELECT cpc.code,
                   COALESCE(cd_exact.description_en,
                            cd_prefix.description_en, '') AS description,
                   COUNT(DISTINCT p.id) AS count
            FROM patent_schema.patents p,
                 LATERAL unnest(p.cpc_codes) AS cpc(code)
            LEFT JOIN patent_schema.cpc_descriptions cd_exact
                ON cd_exact.code = cpc.code
            LEFT JOIN LATERAL (
                SELECT description_en FROM patent_schema.cpc_descriptions
                WHERE cpc.code LIKE code || '%'
                ORDER BY length(code) DESC
                LIMIT 1
            ) cd_prefix ON cd_exact.code IS NULL
            WHERE {where}
              AND p.cpc_codes IS NOT NULL
              AND array_length(p.cpc_codes, 1) > 0
            GROUP BY cpc.code, COALESCE(cd_exact.description_en, cd_prefix.description_en, '')
            ORDER BY count DESC
            LIMIT ${limit_idx}
        """

        logger.debug(
            "query_top_cpc_codes",
            technology=technology,
            limit=limit,
        )

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [
                CpcCount(code=row["code"], description=row["description"], count=row["count"])
                for row in rows
            ]

    # -----------------------------------------------------------------------
    # CORDIS-Projekt-Abfragen
    # -----------------------------------------------------------------------

    async def count_projects_by_year(
        self,
        technology: str,
        *,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> list[YearCount]:
        """Projektanzahl pro Startjahr für eine Technologie.

        CORDIS-Projekte sind per Definition EU-finanziert,
        daher kein european_only-Filter nötig.

        Args:
            technology: Suchbegriff für Volltextsuche.
            start_year: Erstes Jahr (inklusiv).
            end_year: Letztes Jahr (inklusiv).

        Returns:
            Liste von Dicts mit 'year' (int) und 'count' (int),
            sortiert aufsteigend nach Jahr.
        """
        conditions = ["p.search_vector @@ plainto_tsquery('english', $1)"]
        params: list[Any] = [technology]
        idx = 2

        if start_year is not None:
            conditions.append(f"EXTRACT(YEAR FROM p.start_date)::int >= ${idx}")
            params.append(start_year)
            idx += 1

        if end_year is not None:
            conditions.append(f"EXTRACT(YEAR FROM p.start_date)::int <= ${idx}")
            params.append(end_year)
            idx += 1

        where = " AND ".join(conditions)

        sql = f"""
            SELECT EXTRACT(YEAR FROM p.start_date)::int AS year,
                   COUNT(*) AS count
            FROM cordis_schema.projects p
            WHERE {where}
              AND p.start_date IS NOT NULL
            GROUP BY year
            ORDER BY year
        """

        logger.debug(
            "query_projects_by_year",
            technology=technology,
            start_year=start_year,
            end_year=end_year,
        )

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [YearCount(year=row["year"], count=row["count"]) for row in rows]

    async def count_projects_by_country(
        self,
        technology: str,
        *,
        start_year: int | None = None,
        end_year: int | None = None,
        european_only: bool = False,
        limit: int = 20,
    ) -> list[CountryCount]:
        """Projektanzahl pro Land (über cordis_schema.organizations).

        Zählt Projekte pro Organisation-Land via JOIN. Ein Projekt kann
        mehrere Länder haben (Konsortium), daher COUNT(DISTINCT project_id).

        Args:
            technology: Suchbegriff für Volltextsuche.
            start_year: Erstes Jahr (inklusiv).
            end_year: Letztes Jahr (inklusiv).
            european_only: Nur EU/EEA-Länder berücksichtigen.
            limit: Maximale Anzahl Länder (Top-N).

        Returns:
            Liste von Dicts mit 'country' (str, ISO-2) und 'count' (int),
            absteigend sortiert nach count.
        """
        conditions = ["p.search_vector @@ plainto_tsquery('english', $1)"]
        params: list[Any] = [technology]
        idx = 2

        if start_year is not None:
            conditions.append(f"p.start_date >= make_date(${idx}, 1, 1)")
            params.append(start_year)
            idx += 1

        if end_year is not None:
            conditions.append(f"p.start_date <= make_date(${idx}, 12, 31)")
            params.append(end_year)
            idx += 1

        if european_only:
            conditions.append(f"o.country = ANY(${idx}::text[])")
            params.append(list(EU_EEA_COUNTRIES))
            idx += 1

        where = " AND ".join(conditions)
        params.append(limit)
        limit_idx = idx

        sql = f"""
            SELECT o.country,
                   COUNT(DISTINCT o.project_id) AS count
            FROM cordis_schema.projects p
            JOIN cordis_schema.organizations o ON o.project_id = p.id
            WHERE {where}
              AND o.country IS NOT NULL
              AND o.country != ''
            GROUP BY o.country
            ORDER BY count DESC
            LIMIT ${limit_idx}
        """

        logger.debug(
            "query_projects_by_country",
            technology=technology,
            european_only=european_only,
            limit=limit,
        )

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [CountryCount(country=row["country"], count=row["count"]) for row in rows]

    # -----------------------------------------------------------------------
    # Publikations-Abfragen (CRIT-1: CORDIS_LINKED-Scope)
    # -----------------------------------------------------------------------

    async def count_cordis_publications(
        self,
        technology: str,
        *,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> int:
        """Gesamtzahl CORDIS-Projekt-Publikationen für eine Technologie.

        Master-Query für das Header-Summary (UC1 ``total_publications``).
        Nutzt den Scope ``PublicationScope.CORDIS_LINKED`` aus
        :mod:`shared.domain.publication_definitions`.

        **Kritisch für CRIT-1:** publication-svc (UC13) verwendet dieselbe
        SQL-Definition in ``publication_summary()``.  Beide Services müssen
        für dieselben Parameter identische Zahlen liefern — sonst ergibt
        sich die früher beobachtete Divergenz Header ≠ UC13 (Faktor bis
        1580 bei mRNA).

        Args:
            technology: Suchbegriff für Volltextsuche (``plainto_tsquery``).
            start_year: Erstes Jahr (inklusiv), ``None`` = unbeschränkt.
            end_year: Letztes Jahr (inklusiv), ``None`` = unbeschränkt.

        Returns:
            Gesamtzahl der Publikationen aus ``cordis_schema.publications``,
            deren zugehöriges Projekt die Volltext-Suche matcht und im
            Zeitraum ``[start_year, end_year]`` startet.
        """
        # SQL-Parameter dynamisch aufbauen, damit None-Filter wegfallen.
        conditions = ["p.search_vector @@ plainto_tsquery('english', $1)"]
        params: list[Any] = [technology]
        idx = 2

        if start_year is not None:
            conditions.append(f"p.start_date >= make_date(${idx}, 1, 1)")
            params.append(start_year)
            idx += 1

        if end_year is not None:
            conditions.append(f"p.start_date < make_date(${idx} + 1, 1, 1)")
            params.append(end_year)
            idx += 1

        where = " AND ".join(conditions)

        sql = f"""
            SELECT COUNT(*) AS total_publications
            FROM cordis_schema.publications pub
            JOIN cordis_schema.projects p ON pub.project_id = p.id
            WHERE {where}
        """

        logger.debug(
            "query_cordis_publications",
            technology=technology,
            start_year=start_year,
            end_year=end_year,
        )

        async with self._pool.acquire() as conn:
            count = await conn.fetchval(sql, *params)
            return int(count or 0)

    async def funding_by_year(
        self,
        technology: str,
        *,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> list[FundingYear]:
        """EU-Förderung (ec_max_contribution) pro Jahr für eine Technologie.

        Aggregiert über cordis_schema.projects. CORDIS-Projekte sind per
        Definition EU-finanziert, daher kein european_only-Filter nötig.

        Args:
            technology: Suchbegriff für Volltextsuche.
            start_year: Erstes Jahr (inklusiv).
            end_year: Letztes Jahr (inklusiv).

        Returns:
            Liste von Dicts mit 'year' (int), 'funding' (float, Euro)
            und 'count' (int, Anzahl geförderter Projekte),
            sortiert aufsteigend nach Jahr.
        """
        conditions = ["p.search_vector @@ plainto_tsquery('english', $1)"]
        params: list[Any] = [technology]
        idx = 2

        if start_year is not None:
            conditions.append(f"EXTRACT(YEAR FROM p.start_date)::int >= ${idx}")
            params.append(start_year)
            idx += 1

        if end_year is not None:
            conditions.append(f"EXTRACT(YEAR FROM p.start_date)::int <= ${idx}")
            params.append(end_year)
            idx += 1

        where = " AND ".join(conditions)

        sql = f"""
            SELECT EXTRACT(YEAR FROM p.start_date)::int AS year,
                   COALESCE(SUM(p.ec_max_contribution), 0) AS funding,
                   COUNT(*) AS count
            FROM cordis_schema.projects p
            WHERE {where}
              AND p.start_date IS NOT NULL
              AND p.ec_max_contribution IS NOT NULL
            GROUP BY year
            ORDER BY year
        """

        logger.debug(
            "query_funding_by_year",
            technology=technology,
            start_year=start_year,
            end_year=end_year,
        )

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [
                FundingYear(year=row["year"], funding=float(row["funding"]), count=row["count"])
                for row in rows
            ]

    # -----------------------------------------------------------------------
    # Materialized-View-basierte Abfragen (für voraggregierte Daten)
    # -----------------------------------------------------------------------

    async def patent_counts_from_mv(
        self,
        cpc_code: str,
        *,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> list[YearCount]:
        """Patentanzahl pro Jahr aus Materialized View (CPC-basiert).

        Nutzt cross_schema.mv_yearly_tech_counts — schneller als
        Live-Query, aber nur für bekannte CPC-Codes verfügbar.
        Ideal für Dashboard-Aggregationen ohne Freitext-Suche.

        Args:
            cpc_code: CPC-Code (z.B. 'H04W') als Technologie-Identifikator.
            start_year: Erstes Jahr (inklusiv).
            end_year: Letztes Jahr (inklusiv).

        Returns:
            Liste von Dicts mit 'year' (int) und 'count' (int).
        """
        conditions = ["technology = $1"]
        params: list[Any] = [cpc_code]
        idx = 2

        if start_year is not None:
            conditions.append(f"year >= ${idx}")
            params.append(start_year)
            idx += 1

        if end_year is not None:
            conditions.append(f"year <= ${idx}")
            params.append(end_year)
            idx += 1

        where = " AND ".join(conditions)

        sql = f"""
            SELECT year, patent_count AS count
            FROM cross_schema.mv_yearly_tech_counts
            WHERE {where}
            ORDER BY year
        """

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [YearCount(year=row["year"], count=row["count"]) for row in rows]

    async def country_distribution_from_mv(
        self,
        *,
        start_year: int | None = None,
        end_year: int | None = None,
        european_only: bool = False,
        limit: int = 20,
    ) -> list[CountryCount]:
        """Länderverteilung aus Materialized View.

        Nutzt cross_schema.mv_patent_country_distribution — voraggregiert
        aus dem unnest-Join, der bei 154M Zeilen teuer wäre.

        Args:
            start_year: Erstes Jahr (inklusiv).
            end_year: Letztes Jahr (inklusiv).
            european_only: Nur EU/EEA-Länder berücksichtigen.
            limit: Maximale Anzahl Länder.

        Returns:
            Liste von Dicts mit 'country' (str) und 'count' (int).
        """
        conditions: list[str] = []
        params: list[Any] = []
        idx = 1

        if start_year is not None:
            conditions.append(f"year >= ${idx}")
            params.append(start_year)
            idx += 1

        if end_year is not None:
            conditions.append(f"year <= ${idx}")
            params.append(end_year)
            idx += 1

        if european_only:
            conditions.append(f"country_code = ANY(${idx}::text[])")
            params.append(list(EU_EEA_COUNTRIES))
            idx += 1

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(limit)
        limit_idx = idx

        sql = f"""
            SELECT country_code AS country,
                   SUM(patent_count) AS count
            FROM cross_schema.mv_patent_country_distribution
            {where}
            GROUP BY country_code
            ORDER BY count DESC
            LIMIT ${limit_idx}
        """

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [CountryCount(country=row["country"], count=row["count"]) for row in rows]

    async def project_counts_from_mv(
        self,
        *,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> list[YearCount]:
        """Projektanzahl pro Jahr aus Materialized View.

        Nutzt cross_schema.mv_project_counts_by_year — aggregiert
        über alle Frameworks (FP7, H2020, HORIZON).

        Args:
            start_year: Erstes Jahr (inklusiv).
            end_year: Letztes Jahr (inklusiv).

        Returns:
            Liste von Dicts mit 'year' (int) und 'count' (int).
        """
        conditions: list[str] = []
        params: list[Any] = []
        idx = 1

        if start_year is not None:
            conditions.append(f"year >= ${idx}")
            params.append(start_year)
            idx += 1

        if end_year is not None:
            conditions.append(f"year <= ${idx}")
            params.append(end_year)
            idx += 1

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        sql = f"""
            SELECT year,
                   SUM(project_count) AS count
            FROM cross_schema.mv_project_counts_by_year
            {where}
            GROUP BY year
            ORDER BY year
        """

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [YearCount(year=row["year"], count=row["count"]) for row in rows]

    # -----------------------------------------------------------------------
    # Health Check
    # -----------------------------------------------------------------------

    async def health_check(self) -> dict[str, Any]:
        """Datenbank-Health-Check: Verbindung und Basisdaten prüfen.

        Führt leichtgewichtige Zählung durch, um sicherzustellen,
        dass die Schemas und Tabellen erreichbar sind.

        Returns:
            Dict mit 'status', 'pg_version', 'total_patents', 'total_projects'.
        """
        async with self._pool.acquire() as conn:
            version = await conn.fetchval("SELECT version()")
            patent_count = await conn.fetchval(
                "SELECT COUNT(*) FROM patent_schema.patents"
            )
            project_count = await conn.fetchval(
                "SELECT COUNT(*) FROM cordis_schema.projects"
            )
            return {
                "status": "healthy",
                "pg_version": version,
                "total_patents": patent_count,
                "total_projects": project_count,
            }
