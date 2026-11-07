import unittest
from unittest.mock import MagicMock, patch
from types import ModuleType
import sys

# Optional Google client libraries are not required for offline unit tests.
with patch.dict(sys.modules, {
    'google.oauth2': ModuleType('google.oauth2'),
    'google.oauth2.credentials': MagicMock(),
    'google.auth': ModuleType('google.auth'),
    'google.auth.transport': ModuleType('google.auth.transport'),
    'google.auth.transport.requests': MagicMock(),
    'googleapiclient': ModuleType('googleapiclient'),
    'googleapiclient.discovery': MagicMock(),
}):
    from app.services import google_forms


class ThreeQuestionFormCreationTests(unittest.TestCase):
    @patch.object(google_forms, 'get_forms_service')
    def test_three_questions_native_other_and_mapping(self, mock_service):
        service = MagicMock()
        mock_service.return_value = service
        service.forms.return_value.create.return_value.execute.return_value = {'formId': 'google1'}
        service.forms.return_value.batchUpdate.return_value.execute.return_value = {
            'replies': [{'createItem': {'questionId': [qid]}} for qid in ('name', 'q1', 'q2', 'q3')]
        }
        service.forms.return_value.get.return_value.execute.return_value = {'responderUri': 'https://example.test/form'}
        fid, uri, triples = google_forms.create_google_form([{
            'pmid': '100', 'title': 'My Paper',
            'resources': [{'id': 3, 'name': 'Microscope'}],
        }], batch_id=7, researcher_name='Aileen J. Anderson')
        create_body = service.forms.return_value.create.call_args.kwargs['body']
        self.assertEqual(create_body['info']['title'], 'SCRC Publication Attribution Verification')
        self.assertEqual(create_body['info']['documentTitle'],
                         'SCRC Verification | Batch #7 | Aileen J. Anderson | 1 publication(s)')
        self.assertEqual((fid, uri, triples), ('google1', 'https://example.test/form', [('q1', 'q2', 'q3')]))
        payload = service.forms.return_value.batchUpdate.call_args.kwargs['body']
        questions = [req['createItem']['item']['questionItem']['question'] for req in payload['requests']]
        self.assertEqual(len(questions), 4)
        name_item = payload['requests'][0]['createItem']['item']
        self.assertEqual(name_item['title'], 'Your full name')
        self.assertTrue(questions[0]['required'])
        self.assertEqual(questions[0]['textQuestion'], {'paragraph': False})
        questions = questions[1:]
        self.assertEqual([opt['value'] for opt in questions[0]['choiceQuestion']['options']], ['Yes', 'No', 'Unsure'])
        self.assertEqual(questions[1]['choiceQuestion']['options'][-1], {'value': 'Other (not listed)'})
        self.assertFalse(any(opt.get('isOther') for opt in questions[1]['choiceQuestion']['options']))
        self.assertEqual([opt['value'] for opt in questions[2]['choiceQuestion']['options']], ['Critical', 'Significant', 'Minor'])
        self.assertFalse(questions[2]['required'])

    @patch.object(google_forms, 'get_forms_service')
    def test_name_question_does_not_shift_publication_question_ids(self, mock_service):
        service = MagicMock()
        mock_service.return_value = service
        service.forms.return_value.create.return_value.execute.return_value = {'formId': 'google2'}
        qids = ('name', 'a_yes', 'a_equipment', 'a_criticality',
                'b_yes', 'b_equipment', 'b_criticality')
        service.forms.return_value.batchUpdate.return_value.execute.return_value = {
            'replies': [{'createItem': {'questionId': [qid]}} for qid in qids]
        }
        service.forms.return_value.get.return_value.execute.return_value = {'responderUri': 'https://example.test/form2'}
        _, _, triples = google_forms.create_google_form([
            {'pmid': '101', 'title': 'First Paper', 'resources': [{'id': 1, 'name': 'A'}]},
            {'pmid': '102', 'title': 'Second Paper', 'resources': [{'id': 2, 'name': 'B'}]},
        ])
        self.assertEqual(triples, [
            ('a_yes', 'a_equipment', 'a_criticality'),
            ('b_yes', 'b_equipment', 'b_criticality'),
        ])
        self.assertEqual(len(service.forms.return_value.batchUpdate.call_args.kwargs['body']['requests']), 7)


if __name__ == '__main__':
    unittest.main()
