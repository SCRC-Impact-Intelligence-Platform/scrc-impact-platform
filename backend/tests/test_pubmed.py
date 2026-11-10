import unittest
from datetime import date
from unittest.mock import patch
import xml.etree.ElementTree as ET
from app.services import pubmed

SAMPLE = """<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article><ArticleTitle>Test <i>Title</i></ArticleTitle><AuthorList><Author><LastName>Lee</LastName><Initials>AB</Initials></Author></AuthorList><Journal><Title>Journal X</Title><JournalIssue><PubDate><Year>2026</Year><Month>Oct</Month><Day>12</Day></PubDate></JournalIssue></Journal><Abstract><AbstractText Label="BACKGROUND">Some <b>bold</b> text.</AbstractText><AbstractText Label="RESULTS">Good result.</AbstractText></Abstract></Article></MedlineCitation><PubmedData><ArticleIdList><ArticleId IdType="doi">10.1234/test</ArticleId></ArticleIdList></PubmedData></PubmedArticle></PubmedArticleSet>"""

class TestPubMed(unittest.TestCase):
    def test_months(self):
        self.assertEqual(pubmed.months_ago(date(2026, 11, 1)), date(2026, 8, 1))
        self.assertEqual(pubmed.months_ago(date(2024, 5, 31)), date(2024, 2, 29))
        self.assertEqual(pubmed.months_ago(date(2026, 11, 1), 36), date(2023, 11, 1))

    @patch.object(pubmed, "_request")
    def test_pagination_over_100(self, req):
        req.side_effect = [
            {"esearchresult": {"count": "102", "idlist": [str(i) for i in range(100)]}},
            {"esearchresult": {"count": "102", "idlist": ["100", "101"]}},
        ]
        self.assertEqual(len(pubmed.search_publications_by_orcid("id", start_date=date(2026, 8, 1), end_date=date(2026, 11, 1))), 102)
        self.assertEqual(req.call_count, 2)
        self.assertEqual(req.call_args_list[1].args[1]["retstart"], 100)

    def test_parse_doi_and_structured_abstract(self):
        doc = ET.fromstring(SAMPLE)
        paper = pubmed._parse_article(doc.find("PubmedArticle"))
        self.assertEqual(paper["doi"], "10.1234/test")
        self.assertEqual(paper["title"], "Test Title")
        self.assertIn("BACKGROUND: Some bold text.", paper["abstract"])
        self.assertIn("RESULTS: Good result.", paper["abstract"])

    @patch.object(pubmed, "_request")
    def test_efetch_batches(self, req):
        req.return_value = ET.fromstring(SAMPLE)
        pubmed.fetch_publications([str(i) for i in range(205)])
        self.assertEqual(req.call_count, 3)
        self.assertTrue(all(len(call.args[1]["id"].split(",")) <= 100 for call in req.call_args_list))

    @patch.object(pubmed, "_request")
    def test_over_ten_thousand_fails_loudly(self, req):
        req.return_value = {"esearchresult": {"count": "10001", "idlist": ["1"]}}
        with self.assertRaises(RuntimeError):
            pubmed.search_publications_by_orcid("id")

if __name__ == "__main__":
    unittest.main()
