import unittest
from unittest.mock import patch
from datetime import date

from app.services import pubmed


class NameDiscoveryTests(unittest.TestCase):
    def test_author_query(self):
        self.assertEqual(pubmed.author_name_query("Aileen J. Anderson"), "Anderson AJ[au]")
        self.assertEqual(pubmed.author_name_query("Jane Smith"), "Smith J[au]")

    def test_author_affiliation_query(self):
        query = pubmed.author_affiliation_query("Muhammad Aslam")
        self.assertIn("Aslam M[au]", query)
        self.assertIn('"UC Irvine"[ad]', query)
        self.assertIn('"University of California, Irvine"[ad]', query)
        self.assertIn(" AND ", query)

    @patch.object(pubmed, "_request")
    def test_name_search_preserves_window_and_pagination(self, request):
        request.return_value = {"esearchresult": {"count": "1", "idlist": ["123"]}}
        result = pubmed.search_publications_by_name("Jane Smith", start_date=date(2026, 8, 1), end_date=date(2026, 11, 1))
        self.assertEqual(result, ["123"])
        params = request.call_args.args[1]
        self.assertEqual(params["term"], pubmed.author_affiliation_query("Jane Smith"))
        self.assertEqual(params["datetype"], "pdat")
        self.assertEqual(params["mindate"], "2026/08/01")

    @patch.object(pubmed, "_request")
    def test_orcid_search_remains_unrestricted(self, request):
        request.return_value = {"esearchresult": {"count": "1", "idlist": ["123"]}}
        result = pubmed.search_publications_by_orcid("0000-0002-8203-8891")
        self.assertEqual(result, ["123"])
        self.assertEqual(request.call_args.args[1]["term"], "orcid 0000-0002-8203-8891[auid]")

    @patch.object(pubmed, "fetch_publications", return_value=[{"pmid": "123"}])
    @patch.object(pubmed, "search_publications_by_name", return_value=["123"])
    def test_discovery_uses_name_without_orcid(self, name_search, fetch):
        self.assertEqual(pubmed.discover_publications(name="Jane Smith"), [{"pmid": "123"}])
        name_search.assert_called_once()


if __name__ == "__main__":
    unittest.main()
