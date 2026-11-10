"""PubMed author discovery: ORCID preferred, name fallback, EFetch metadata."""
from calendar import monthrange
from datetime import date
import json
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.services.pubdates import date_parts, structured_date_parts

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PAGE_SIZE = 100
FETCH_BATCH_SIZE = 100
# Keep calls conservatively below NCBI's unauthenticated 3 requests/sec limit.
_LAST_REQUEST = 0.0


def _request(endpoint: str, params: dict, *, xml: bool = False):
    global _LAST_REQUEST
    wait = 0.4 - (time.monotonic() - _LAST_REQUEST)
    if wait > 0:
        time.sleep(wait)
    query = {**params, "tool": "scrc_impact_platform", "retmode": "xml" if xml else "json"}
    request = Request(f"{BASE_URL}/{endpoint}?{urlencode(query)}", headers={"User-Agent": "SCRC-Impact-Platform/0.1"})
    _LAST_REQUEST = time.monotonic()
    with urlopen(request, timeout=30) as response:
        payload = response.read()
    return ET.fromstring(payload) if xml else json.loads(payload)


def months_ago(today: date, months: int = 3) -> date:
    if months < 0:
        raise ValueError("months must be nonnegative")
    year, month_index = divmod(today.year * 12 + today.month - 1 - months, 12)
    month = month_index + 1
    return date(year, month, min(today.day, monthrange(year, month)[1]))


def author_name_query(name: str) -> str:
    """Basic LastName + initials PubMed [au] query; review ambiguous matches."""
    parts = name.replace(",", " ").split()
    if len(parts) < 2:
        raise ValueError("Full researcher name (given name and surname) is required for name search")
    surname = parts[-1]
    initials = "".join(part[0] for part in parts[:-1] if part[0].isalpha())[:2]
    if not initials or not surname[0].isalpha():
        raise ValueError("Invalid researcher name for PubMed author search")
    return f"{surname} {initials}[au]"


# Affiliation restriction for researchers without ORCID. PubMed [ad] searches
# affiliations across the citation, not necessarily the matched author's own.
UCI_AFFILIATION_QUERY = (
    '("University of California Irvine"[ad] '
    'OR "University of California, Irvine"[ad] '
    'OR "UC Irvine"[ad] '
    'OR "UCIRVINE"[ad])'
)


def author_affiliation_query(name: str) -> str:
    """Narrow name-only discovery to publications mentioning UCI affiliation."""
    return f"({author_name_query(name)}) AND {UCI_AFFILIATION_QUERY}"


def _search_publication_ids(term: str, *, start_date: date | None = None, end_date: date | None = None) -> list[str]:
    end_date = end_date or date.today()
    start_date = start_date or months_ago(end_date)
    if start_date > end_date:
        raise ValueError("start_date must be <= end_date")
    base = {"db": "pubmed", "term": term, "sort": "pub_date",
            "datetype": "pdat", "mindate": start_date.strftime("%Y/%m/%d"),
            "maxdate": end_date.strftime("%Y/%m/%d"), "retmax": PAGE_SIZE}
    ids = []
    offset = 0
    while True:
        result = _request("esearch.fcgi", {**base, "retstart": offset})["esearchresult"]
        count = int(result["count"])
        if count > 10000:
            raise RuntimeError(f"ESearch matched {count} records; PubMed 10,000 record retrieval limit requires smaller date windows")
        page = result["idlist"]
        if not page and offset < count:
            raise RuntimeError("Unexpected empty PubMed ESearch page")
        ids.extend(page)
        offset += len(page)
        if offset >= count:
            return list(dict.fromkeys(ids))


def search_publications_by_orcid(orcid: str, *, start_date: date | None = None, end_date: date | None = None) -> list[str]:
    return _search_publication_ids(f"orcid {orcid}[auid]", start_date=start_date, end_date=end_date)


def search_publications_by_name(name: str, *, start_date: date | None = None, end_date: date | None = None) -> list[str]:
    return _search_publication_ids(author_affiliation_query(name), start_date=start_date, end_date=end_date)


def _text(node):
    return "".join(node.itertext()).strip() if node is not None else None


def _parse_article(article: ET.Element) -> dict | None:
    pmid = article.findtext("./MedlineCitation/PMID")
    if not pmid:
        return None
    content = article.find("./MedlineCitation/Article")
    if content is None:
        return None
    title = _text(content.find("./ArticleTitle")) or "(Untitled)"
    authors = []
    for author in content.findall("./AuthorList/Author"):
        collective = author.findtext("CollectiveName")
        if collective:
            authors.append(collective)
        else:
            last = author.findtext("LastName") or ""
            initials = author.findtext("Initials") or ""
            name = " ".join(part for part in (last, initials) if part)
            if name:
                authors.append(name)
    doi = None
    for node in article.findall("./PubmedData/ArticleIdList/ArticleId"):
        if node.get("IdType") == "doi" and node.text:
            doi = node.text.strip()
            break
    if not doi:
        for node in content.findall("./ELocationID"):
            if node.get("EIdType") == "doi" and node.text:
                doi = node.text.strip()
                break
    sections = []
    for node in content.findall("./Abstract/AbstractText"):
        body = _text(node)
        if body:
            label = node.get("Label")
            sections.append(f"{label}: {body}" if label else body)
    abstract = "\n\n".join(sections) or None
    pubdate = content.find("./Journal/JournalIssue/PubDate")
    date_value = " ".join(x for x in (
        pubdate.findtext("Year") if pubdate is not None else None,
        pubdate.findtext("Month") if pubdate is not None else None,
        pubdate.findtext("Day") if pubdate is not None else None,
    ) if x) or (pubdate.findtext("MedlineDate") if pubdate is not None else None)
    structured = pubdate is not None and structured_date_parts(
        pubdate.findtext("Year"), pubdate.findtext("Month"), pubdate.findtext("Day")
    )
    journal = content.findtext("./Journal/Title")
    return {"pmid": pmid, "title": title, "authors": authors, "journal": journal,
            "publication_date": date_value, "doi": doi, "abstract": abstract,
            **(structured or date_parts(date_value))}


def fetch_publications(pmids: list[str]) -> list[dict]:
    papers = []
    for start in range(0, len(pmids), FETCH_BATCH_SIZE):
        batch = pmids[start:start + FETCH_BATCH_SIZE]
        root = _request("efetch.fcgi", {"db": "pubmed", "id": ",".join(batch)}, xml=True)
        for node in root.findall("./PubmedArticle"):
            paper = _parse_article(node)
            if paper:
                papers.append(paper)
    return papers


def discover_publications(orcid: str | None = None, *, name: str | None = None, start_date: date | None = None, end_date: date | None = None) -> list[dict]:
    if orcid:
        pmids = search_publications_by_orcid(orcid, start_date=start_date, end_date=end_date)
    elif name:
        pmids = search_publications_by_name(name, start_date=start_date, end_date=end_date)
    else:
        raise ValueError("Researcher ORCID or name is required")
    return fetch_publications(pmids)
