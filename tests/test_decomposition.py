""" Unit tests for Decompose Job Description service  """
from unittest import TestCase
from services.decomposition import (
    Sentencizer,
    DecomposeJobDescription
)
from nameko.testing.services import worker_factory


class TestFrameworkEmbeddingServices(TestCase):
    def setUp(self):
        pass

    def test_sentencizer(self):
        """ The fundamental NLP pipeline provider should break up a doc into sentences
        """
        sentencizer = Sentencizer()
        doc = sentencizer.decompose("This is a sentence. This is another sentence.")
        assert len(doc.split('\n')) == 3

    def test_decompose_job_decription(self):
        """ The decompose service should break up a raw doc into sentences
        """
        decompose_job_description = worker_factory(DecomposeJobDescription)
        decompose_job_description.decomposer\
                                 .decompose\
                                 .return_value =\
            'substatement,substatementID,jdx_class_a,jdx_property_a,jdx_class_b,jdx_property_b,jdx_class_c,jdx_property_c\nThis is a sentence.,2b6c1ae3-b6b4-59f3-b262-981443064639,,competencycompetency,,,,\nThis is another sentence.,383816ef-8009-53a5-b90e-f8057536cdd2,,competencycompetency,,,,\n'

        doc = decompose_job_description.decompose("This is a sentence. This is another sentence.")
        assert len(doc.split('\n')) == 3
