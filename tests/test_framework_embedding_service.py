""" Unit tests for framework service  """
from utils.framework_similarity import FrameworkSimilarity as _FrameworkSimilarity
from utils.parser.clearinghouse import (
    read_excel_with_formatting,
    induce_tags
)
from services.frameworks import Frameworks
from services.embeddings import Embeddings
import pandas as pd
from io import StringIO
from unittest import TestCase
from fakeredis import FakeStrictRedis
from nameko.testing.services import worker_factory


class TestFrameworkEmbeddingServices(TestCase):
    def setUp(self):
        self.mock_redis = FakeStrictRedis()
        self.mock_cybersecurity_framework =\
            bytes(
                """value,numeric_tag,uuid\nAttack stages,"section 4., row=961",5908761c-aead-592e-bf1d-49ad739c682a\nFootprinting and scanning,"section 4., row=962",78adab7a-91c1-5bdb-9a36-49bd957ff0c8\nEnumeration,"section 4., row=963",d88055e4-2636-5374-9e7f-129d0220add7\nGaining access,"section 4., row=964",7bc159f6-9e24-518d-9bfc-8e693bd6e172""".encode("utf-8"))

    def tearDown(self):
        del self.mock_redis

    def test_parse_and_write_a_framework(self):
        """ Framework parsing, storing and embedding tests.
        """
        framework_path = './tests/fixtures/frameworks/Cybersecurity-Industry.xls'
        df = read_excel_with_formatting(framework_path,
                                        'Sheet1',
                                        competency_col=0,
                                        skiprows=5)
        df = induce_tags(df)

        frameworks = Frameworks()
        frameworks.client = self.mock_redis

        frameworks.parse_and_write_framework(
            name="cybersecurity",
            path=framework_path,
            provider="clearinghouse",
            provider_args={
                "sheet_name": "Sheet1",
                "competency_col": 0,
                "skiprows": 5
            })

        framework_df = pd.read_csv(
            StringIO(
                frameworks.client
                          .get("cybersecurity")
                          .decode("utf-8"))
        )

        assert len(df.columns) > len(framework_df.columns)
        assert len(df) == len(framework_df)

    def test_generate_and_write_framework_embeddings(self):
        """ Given a framework, generate embeddings for value column, write
            value embeddings and uuids to the embeddings database
        """
        embeddings = worker_factory(Embeddings)
        embeddings.framework_rpc\
                  .get_framework\
                  .return_value = self.mock_cybersecurity_framework

        embeddings.client = self.mock_redis
        embeddings.generate_and_write_framework_embeddings(
            framework_name="cybersecurity"
        )

        cybersecurity_df = pd.read_csv(
            StringIO(
                embeddings.client.get(name="cybersecurity")
                          .decode("utf-8"))
        )

        assert len(cybersecurity_df.columns) == 513
        assert len(cybersecurity_df) == 4

    def test_framework_similarity(self):
        framework_similarity = _FrameworkSimilarity(
            framework_type="",
            framework_dir="./tests/fixtures/text_frameworks"
        )

        frameworks =\
            framework_similarity.framework_recommedation("this is a test")

        assert len(frameworks) == 2

    def test_framework_similarity_service(self):
        framework_similarity = worker_factory(Frameworks)
        mock_file_text = "this is a test"
        framework_similarity.get_raw_text\
                            .return_value = mock_file_text
        framework_similarity.recommend\
                            .return_value = ['Cybersecurity', 'Transportation']

        frameworks = \
            framework_similarity.recommend()

        assert len(frameworks) == 2
