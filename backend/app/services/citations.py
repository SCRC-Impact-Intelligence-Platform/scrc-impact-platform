"""Formatted citations, using the CSL "NLM citation-sequence" style.

PubMed-style authors ("Lee AB") are split into the family and given names CSL expects.
Volume, issue and pages aren't stored yet, so citations leave them out.
"""

import re
from pathlib import Path

from citeproc import Citation, CitationItem, CitationStylesBibliography, CitationStylesStyle, formatter
from citeproc.source.json import CiteProcJSON

from app.models.publication import Publication

_STYLE = Path(__file__).resolve().parents[1] / "data" / "csl" / "nlm-citation-sequence.csl"
_INITIALS = re.compile(r"^[A-Z]{1,5}$")


def _csl_author(author: str) -> dict:
    family, _, initials = author.rpartition(" ")
    if family and _INITIALS.match(initials):
        # Spaced so CSL keeps every initial, not just the first.
        return {"family": family, "given": " ".join(initials)}
    return {"literal": author}  # a collective author, e.g. "COVID-19 Study Group"


def _csl_item(publication: Publication) -> dict:
    item = {
        "id": publication.pmid,
        "type": "article-journal",
        "title": publication.title,
        "author": [_csl_author(author) for author in publication.authors],
        "PMID": publication.pmid,
    }
    if publication.journal:
        item["container-title"] = publication.journal
    if publication.doi:
        item["DOI"] = publication.doi
    parts = [publication.publication_year, publication.publication_month, publication.publication_day]
    parts = parts[: parts.index(None)] if None in parts else parts
    if parts:
        item["issued"] = {"date-parts": [parts]}
    return item


def format_citations(publications: list[Publication]) -> dict[str, str]:
    """Citation text for each publication, keyed by PMID."""
    if not publications:
        return {}
    style = CitationStylesStyle(str(_STYLE), validate=False)
    bibliography = CitationStylesBibliography(
        style, CiteProcJSON([_csl_item(p) for p in publications]), formatter.plain
    )
    for publication in publications:
        citation = Citation([CitationItem(publication.pmid.lower())])
        bibliography.register(citation)
        bibliography.cite(citation, lambda item: None)
    entries = [str(entry) for entry in bibliography.bibliography()]
    return {p.pmid: entry for p, entry in zip(publications, entries)}
