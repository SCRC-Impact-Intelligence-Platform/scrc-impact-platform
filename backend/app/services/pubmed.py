import json
from urllib.parse import urlencode
from urllib.request import urlopen

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def request_pubmed(endpoint: str, params: dict) -> dict:
    """Send a request to NCBI E-utilities."""

    params["tool"] = "scrc_impact_platform"
    params["retmode"] = "json"

    url = f"{BASE_URL}/{endpoint}?{urlencode(params)}"

    with urlopen(url, timeout=30) as response:
        return json.load(response)


def search_publications_by_orcid(
    orcid: str,
    limit: int = 10,
) -> list[str]:
    """Search PubMed and return a list of PMIDs."""

    query = f"orcid {orcid}[auid]"

    data = request_pubmed(
        "esearch.fcgi",
        {
            "db": "pubmed",
            "term": query,
            "retmax": limit,
            "sort": "pub_date",
        },
    )

    return data["esearchresult"]["idlist"]


def fetch_publications(pmids: list[str]) -> list[dict]:
    """Fetch publication summaries from PubMed."""

    if not pmids:
        return []

    data = request_pubmed(
        "esummary.fcgi",
        {
            "db": "pubmed",
            "id": ",".join(pmids),
            "version": "2.0",
        },
    )

    publications = []

    for pmid in data["result"]["uids"]:
        item = data["result"][pmid]

        publications.append(
            {
                "pmid": pmid,
                "title": item.get("title"),
                "authors": [
                    author["name"]
                    for author in item.get("authors", [])
                ],
                "journal": item.get("fulljournalname"),
                "publication_date": item.get("pubdate"),
            }
        )

    return publications


def discover_publications(orcid: str) -> list[dict]:
    """Discover publications for one researcher."""

    pmids = search_publications_by_orcid(orcid)

    return fetch_publications(pmids)