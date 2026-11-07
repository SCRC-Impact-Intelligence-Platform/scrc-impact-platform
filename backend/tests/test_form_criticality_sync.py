import unittest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.researcher import Researcher  # noqa: F401
from app.models.resource import Resource  # noqa: F401
from app.models.publication import Publication
from app.models.forms import FormBatch, FormQuestion
from app.models.publication_resource import PublicationResource
from app.services.form_sync import sync_batch


class ThreeQuestionSyncTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.publication = Publication(pmid='123', title='Paper', authors=['Test T'], status='SENT')
        self.db.add(self.publication)
        self.db.flush()
        self.batch = FormBatch(state='SENT')
        self.db.add(self.batch)
        self.db.flush()
        self.question = FormQuestion(batch_id=self.batch.id, publication_id=self.publication.id,
            resource_ids=[3, 4], yes_question_id='yes', resources_question_id='machines', criticality_question_id='crit')
        self.db.add(self.question)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def sync(self, answer, machines=None, criticality=None):
        answers = {'yes': {'textAnswers': {'answers': [{'value': answer}]}}}
        if machines is not None:
            answers['machines'] = {'textAnswers': {'answers': [{'value': v} for v in machines]}}
        if criticality is not None:
            answers['crit'] = {'textAnswers': {'answers': [{'value': criticality}]}}
        return sync_batch(self.db, self.batch, [{'responseId': 'response1', 'answers': answers}])

    def attributions(self):
        return self.db.execute(select(PublicationResource.resource_id, PublicationResource.criticality)).all()

    def test_yes_multiple_machines_inherits_same_criticality(self):
        result = self.sync('Yes', ['3: Machine A', '4: Machine B'], 'Significant')
        self.assertEqual(result['processed'], 1)
        self.assertEqual(self.publication.status, 'CONFIRMED')
        self.assertEqual(set(self.attributions()), {(3, 'SIGNIFICANT'), (4, 'SIGNIFICANT')})

    def test_extra_respondent_name_answer_is_ignored(self):
        answers = {
            'respondent_name_question': {'textAnswers': {'answers': [{'value': 'Example Respondent'}]}},
            'yes': {'textAnswers': {'answers': [{'value': 'Yes'}]}},
            'machines': {'textAnswers': {'answers': [{'value': '3: Machine A'}]}},
            'crit': {'textAnswers': {'answers': [{'value': 'Critical'}]}},
        }
        result = sync_batch(self.db, self.batch, [{'responseId': 'response1', 'answers': answers}])
        self.assertEqual(result['processed'], 1)
        self.assertEqual(self.attributions(), [(3, 'CRITICAL')])
        self.assertFalse(hasattr(self.question, 'respondent_name'))

    def test_no_does_not_create_attribution(self):
        self.assertEqual(self.sync('No')['processed'], 1)
        self.assertEqual(self.publication.status, 'REJECTED')
        self.assertEqual(self.attributions(), [])
        self.assertEqual(self.question.usage_answer, 'No')

    def test_unsure_does_not_create_attribution(self):
        self.assertEqual(self.sync('Unsure')['processed'], 1)
        self.assertEqual(self.publication.status, 'UNSURE')
        self.assertEqual(self.attributions(), [])
        self.assertEqual(self.question.usage_answer, 'Unsure')

    def test_fixed_other_only_is_review_not_confirmed(self):
        self.assertEqual(self.sync('Yes', ['Other (not listed)'], 'Critical')['processed'], 1)
        self.assertEqual(self.publication.status, 'NEEDS_REVIEW')
        self.assertEqual(self.attributions(), [])
        self.assertEqual(self.question.other_resource_text, 'Other (not listed)')
        self.assertEqual(self.question.reported_criticality, 'CRITICAL')

    def test_fixed_other_plus_known_keeps_known_attribution(self):
        self.assertEqual(self.sync('Yes', ['3: Machine A', 'Other (not listed)'], 'Minor')['processed'], 1)
        self.assertEqual(self.publication.status, 'CONFIRMED')
        self.assertEqual(self.attributions(), [(3, 'MINOR')])
        self.assertEqual(self.question.other_resource_text, 'Other (not listed)')

    def test_only_other_is_review_not_confirmed(self):
        self.assertEqual(self.sync('Yes', ['Optical imaging setup'], 'Critical')['processed'], 1)
        self.assertEqual(self.publication.status, 'NEEDS_REVIEW')
        self.assertEqual(self.attributions(), [])
        self.assertEqual(self.question.other_resource_text, 'Optical imaging setup')
        self.assertEqual(self.question.reported_criticality, 'CRITICAL')

    def test_other_plus_known_creates_known_attribution_and_preserves_other(self):
        self.assertEqual(self.sync('Yes', ['3: Machine A', 'Microscopy service'], 'Minor')['processed'], 1)
        self.assertEqual(self.publication.status, 'CONFIRMED')
        self.assertEqual(self.attributions(), [(3, 'MINOR')])
        self.assertEqual(self.question.other_resource_text, 'Microscopy service')

    def test_invalid_yes_does_not_persist(self):
        result = self.sync('Yes', ['3: Machine A'])
        self.assertEqual(result['invalid'], 1)
        self.assertEqual(self.publication.status, 'SENT')
        self.assertEqual(self.batch.state, 'SENT')
        self.assertEqual(self.attributions(), [])

    def test_no_with_criticality_is_invalid(self):
        self.assertEqual(self.sync('No', criticality='Minor')['invalid'], 1)
        self.assertEqual(self.publication.status, 'SENT')


if __name__ == '__main__':
    unittest.main()
