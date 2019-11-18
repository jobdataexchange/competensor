""" Unit tests for build competensor service  """
from json import loads
from joblib import load
from utils.embeddings import UniversalSentenceEncoder
from utils.db import JDXDatabase
from utils.framework_similarity import FrameworkSimilarity
from utils.embeddings import UniversalSentenceEncoder
from services.decomposition import Sentencizer
from services.build_competensor import BuildCompetensorFrameworks
from services.frameworks import (
    Frameworks,
    FrameworkRecommendation,
    GetRawText
)
from competensor import Competensor
from pathlib import Path
from unittest import TestCase, mock
from redis import StrictRedis
from nameko.testing.services import entrypoint_hook, worker_factory
from nameko.testing.utils import get_container
from nameko.runners import ServiceRunner
import requests


class TestCompetensorServiceIntegration(TestCase):
    def setUp(self):
        self.integration_config = \
            {
                "AMQP_URI": "pyamqp://guest:guest@localhost:5673",
                "JDX_DB_URI": "postgresql+psycopg2://postgres:password@localhost:5433/jdx_reference_backend_application",
                "WEB_SERVER_ADDRESS": "0.0.0.0:8000",
                "frameworks":
                    {
                        "clearinghouse": {"directories": ["./tests/fixtures/frameworks"]}
                    },
                "text_frameworks":
                    {
                        "directories": ["./tests/fixtures/text_frameworks"]
                    },
                "model_path": "./linear_5_19.joblib",
                "REDIS_URIS":
                    {
                        "frameworks": "redis://localhost:6380/0",
                        "embeddings": "redis://localhost:6380/1",
                        "sentences": "redis://localhost:6380/2"
                    }
            }

        #  User uplaods an ACME Junior Developer job description for analysis
        with open("./tests/fixtures/job_descriptions/Junior Developer - ACME Corp.docx", 'rb') as obj:
            response = requests.post("http://localhost:8000/upload-job-description-file",
                                     files={"file": obj})
            self.pipeline_id = response.json()['pipelineID']

    def tearDown(self):
        pass

    def test_build_competensor_frameworks(self):
        embedding_client = StrictRedis.from_url(
            self.integration_config["REDIS_URIS"]["embeddings"]
        )
        framework_client = StrictRedis.from_url(
            self.integration_config["REDIS_URIS"]["frameworks"]
        )
        build = worker_factory(BuildCompetensorFrameworks,
                               config=self.integration_config,
                               frameworks_client=framework_client,
                               embeddings_client=embedding_client,
                               universal_sentence_encoder=UniversalSentenceEncoder())

        build.with_providers_soand_store_frameworks()
        for provider, provider_config in self.integration_config['frameworks'].items():
            for directory in provider_config['directories']:
                for file_path in Path(directory).glob("*"):
                    assert framework_client.exists(file_path.stem)

        build.and_convert_frameworks_to_embeddings()
        for provider, provider_config in self.integration_config['frameworks'].items():
            for directory in provider_config['directories']:
                for file_path in Path(directory).glob("*"):
                    assert embedding_client.exists(file_path.stem)

    def test_recommend_a_framework(self):
        framework_client = StrictRedis.from_url(
            self.integration_config["REDIS_URIS"]["frameworks"]
        )
        get_raw_text = JDXDatabase(
                uri=self.integration_config["JDX_DB_URI"]
            ).get_raw_text_from_pipeline
        recommendations = FrameworkSimilarity(
                framework_type="",
                framework_dir=self.integration_config["text_frameworks"]["directories"][0],
            ).framework_recommedation
        recommend = worker_factory(Frameworks,
                                   config=self.integration_config,
                                   client=framework_client,
                                   competency_recommendations=recommendations,
                                   get_raw_text=get_raw_text
                                   )
        number_of_frameworks = 0
        for provider, provider_config in self.integration_config['frameworks'].items():
            for directory in provider_config['directories']:
                number_of_frameworks += len(list(Path(directory).glob("*")))

        response =\
            loads(
                recommend.recommend(self.pipeline_id)
            )

        assert number_of_frameworks == len(response['frameworkRecommendations'])

    def test_match_table(self):
        embedding_client = StrictRedis.from_url(
            self.integration_config["REDIS_URIS"]["embeddings"],
            decode_responses=True
        )
        framework_client = StrictRedis.from_url(
            self.integration_config["REDIS_URIS"]["frameworks"],
            decode_responses=True
        )        
        for provider, provider_config in self.integration_config['frameworks'].items():
            for directory in provider_config['directories']:
                for file_path in Path(directory).glob("*"):
                    a_framework_to_match = file_path.stem
                    break

        JSONLD = JDXDatabase(
                uri=self.integration_config["JDX_DB_URI"]
            ).get_context_object

        components = Sentencizer()
        get_raw_text = JDXDatabase(
                uri=self.integration_config["JDX_DB_URI"]
            ).get_raw_text_from_pipeline

        universal_sentence_encoder = UniversalSentenceEncoder()
        model = load(self.integration_config['model_path'])
        competensor = worker_factory(Competensor,
                                     frameworks=framework_client,
                                     embeddings=embedding_client,
                                     get_raw_text=get_raw_text,
                                     model=model,
                                     jsonld=JSONLD,
                                     components=components,
                                     universal_sentence_encoder=universal_sentence_encoder)
        response =\
            loads(
                competensor.get_match_table_and_jsonld(self.pipeline_id,
                                                       a_framework_to_match)
            )

        assert len(response["match_table"]) > 1
