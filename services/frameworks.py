from json import dumps
from datetime import datetime, timedelta
from nameko.rpc import rpc
from nameko.dependency_providers import Config
from nameko.extensions import DependencyProvider
from nameko_redis import Redis
from uuid import uuid5, NAMESPACE_DNS
from utils.db import JDXDatabase
from utils.framework_similarity import FrameworkSimilarity
from utils.parser.clearinghouse import (
    read_excel_with_formatting,
    induce_tags
)


class GetRawText(DependencyProvider):
    def __init__(self,
                 tablename=None,
                 uri=None):
        self.uri = uri
        self.tablename = tablename

    def setup(self):
        self.uri = self.uri or self.container.config['JDX_DB_URI']
        self.jdx_database = JDXDatabase(uri=self.uri)

    def get_dependency(self, worker_ctx):
        return self.jdx_database.get_raw_text_from_pipeline


class FrameworkRecommendation(DependencyProvider):
    def __init__(self,
                 framework_dir="./frameworks/metadata",
                 framework_type=""):
        self.similiarity =\
            FrameworkSimilarity(framework_dir=framework_dir,
                                framework_type=framework_type)

    def get_dependency(self, worker_ctx):
        return self.similiarity.framework_recommedation


class Frameworks:
    name = "frameworks"

    config = Config()
    client = Redis('frameworks')
    competency_recommendations = FrameworkRecommendation()
    #  todo post 5/31 and also improve recommendation quality
    # industry_recommendations = FrameworkRecommendation()    
    # occupation_recommendations = FrameworkRecommendation()        
    get_raw_text = GetRawText()

    @rpc
    def recommend(self, job_description_id):

        frameworkRecommendations = []

        for recommendation in self.competency_recommendations(
                self.get_raw_text(job_description_id)):
            frameworkRecommendations.append(
                {
                    "value": recommendation[1],
                    "validUntil": str(
                        datetime.utcnow()+timedelta(days=3)
                        ),
                    "frameworkData": {
                        "uuid": str(recommendation[2]),
                        "objectType": "recommendation",
                        "name": recommendation[0]
                    }
                }
            )

        return \
                {
                    "pipelineID": job_description_id,
                    "timestamp": str(datetime.utcnow()),
                    "frameworkRecommendations": frameworkRecommendations
                }
