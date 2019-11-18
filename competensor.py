from io import StringIO
import datetime
import pandas as pd
from itertools import repeat
from joblib import load
from json import loads, dumps
from nameko.dependency_providers import Config
from nameko.rpc import rpc
from nameko_redis import Redis
import numpy as np
from uuid import NAMESPACE_DNS, uuid5
from utils.embeddings import UniversalSentenceEncoder\
    as _UniversalSentenceEncoder
from utils.db import JDXDatabase
from nameko.extensions import DependencyProvider
from services.decomposition import Sentencizer
import web_pdb

class SetupFrameworks(DependencyProvider):
    def __init__(self):
        pass

    def start(self):
        setup = BuildCompetensorFrameworks()
        setup.with_providers_and_store_frameworks()
        setup.and_convert_frameworks_to_embeddings()


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
        #return self.jdx_database.get_raw_text_from_pipeline
        return self.jdx_database


class Decomposer(DependencyProvider):
    def get_dependency(self, worker_ctx):
        return Sentencizer()


class UniversalSentenceEncoder(DependencyProvider):
    def __init__(self,
                 module_url="./tensorflow_models/universal_sentence_encoder/",
                 encoder_type="DAN"):
        self.module_url = module_url
        self.encoder_type = encoder_type

    def setup(self):
        self.universal_sentence_encoder = _UniversalSentenceEncoder(
            module_url=self.module_url,
            encoder_type=self.encoder_type
        )

    def get_dependency(self, worker_ctx):
        return self.universal_sentence_encoder


class Model(DependencyProvider):
    def __init__(self,
                 model_name="linear_5_19.joblib",
                 model_path="./"):
        self.model = None
        self.model_name = model_name
        if model_name:
            self.model = load(
                model_path+model_name
            )

    def get_model_name(self):
        return self.model_name

    def get_dependency(self, worker_ctx):
        return self.model


class Competensor:
    name = "competensor"
    config = Config()
    universal_sentence_encoder = UniversalSentenceEncoder()
    model = Model()

    get_raw_text = GetRawText()
    frameworks = Redis("frameworks")
    embeddings = Redis("embeddings")
    match_table = Redis("match_table")
    components = Decomposer()

    def construct_sentences(self,
                            data_frame=None,
                            sentence_cols=["substatement"]):
        competency_query =\
            'jdx_property_a == "competency"    | \
             jdx_property_b == "competency"    | \
             jdx_property_c == "competency"'
        return pd.Series(
            data_frame.query(competency_query)[sentence_cols]
                      .values
                      .flatten()
        )

    def save_match_table(self, job_description_id, substatement_map, embedding_indices):
        def get_match_table_row(substatement_map, embedding_indices):
            for index, substatementID in zip(embedding_indices, substatement_map.keys()):
                item = substatement_map[substatementID]
                matches = item['matches']

                for data in matches:
                    yield (substatementID,
                           data['recommendationID'],
                           data['name'],
                           data['definedTermSet'],
                           data['termCode'],
                           data['value'],
                           item['substatement'],
                           index)

        # self.match_table.append(
        #     job_description_id,
        #     pd.DataFrame(
        #         data=get_match_table_row(substatement_map, embedding_indices)
        #     ).to_csv(index=False, header=False)
        # )
        self.match_table.set(
            job_description_id,
            pd.DataFrame(
                data=get_match_table_row(substatement_map, embedding_indices)
            ).to_csv(index=False, header=False)
        )

    def get_all_sentences(self,
                          job_description_id):
        sentences_df = pd.read_csv(
            StringIO(
                self.components.decompose(
                    self.get_raw_text.get_raw_text_from_pipeline(
                        job_description_id)))
        )

        return sentences_df

    def get_all_sentence_embeddings(self,
                                    job_description_id,
                                    sentences_df):
        sentence_embeddings =\
            self.universal_sentence_encoder\
                .embed(
                    sentences=self.construct_sentences(
                        data_frame=sentences_df)
                )
        return sentence_embeddings

    def for_all_frameworks_find_matches_and_store(
        self,
        framework_names,
        sentence_embeddings,
        sentences_df,
        threshold,
        substatement_map,
        job_description_id):
        for framework_name in framework_names:

            framework_df = pd.read_csv(
                StringIO(
                    self.frameworks.get(
                        framework_name))
                )

            framework_embeddings = pd.read_csv(
                StringIO(
                    self.embeddings.get(
                        framework_name))
                ).iloc[:, :-1].values

            assert sentence_embeddings.shape[1] == framework_embeddings.shape[1]

            similarities =\
                np.inner(
                    sentence_embeddings,
                    framework_embeddings
                )

            lower_triangle = np.tril_indices(n=similarities.shape[0],
                                             m=similarities.shape[1])
            similarities[lower_triangle] = 0

            sentence_and_framework_statement_indices =\
                np.argwhere(similarities > threshold)

            # values =\
            #     self.model.predict(
            #         similarities[
            #             similarities > threshold
            #             ].flatten()
            #             .reshape((-1, 1))
            #     )
            values = repeat(-1, len(sentence_embeddings))

            flattened_similarities =\
                similarities[
                    similarities > threshold
                    ].flatten()

            if len(flattened_similarities):
                reshaped_similarities =\
                    flattened_similarities.reshape((-1, 1))
                values = \
                    self.model.predict(
                        reshaped_similarities
                )

            embedding_indices_for_save_match_table = []

            for value, (sentence_idx, framework_idx) in zip(
                    values, sentence_and_framework_statement_indices):

                substatementID = str(
                            uuid5(
                                NAMESPACE_DNS, sentences_df.loc[sentence_idx,"substatement"]))

                item = substatement_map.get(substatementID, {"matches": []})
                item["substatement"] = sentences_df.loc[sentence_idx, "substatement"]
                
                if value >= threshold:
                    item["matches"].append(
                        {
                            "recommendationID":
                                framework_df.loc[framework_idx, "uuid"],
                            "name":
                                framework_df.loc[framework_idx, "framework_statement"],
                            "description":
                                "(framework term descriptions TBD later)",
                            "definedTermSet":
                                framework_name,
                            "termCode": "",
                            #     framework_df.loc[framework_idx, "numeric_tag"],
                            "value":
                                value
                        }
                    )


                substatement_map[substatementID] = item
                embedding_indices_for_save_match_table.append(framework_idx)

            self.save_match_table(job_description_id, substatement_map, embedding_indices_for_save_match_table)

            match_table = [
                {
                        "substatementID": key,
                        "substatement": value["substatement"],
                        "matches": value["matches"]
                }
                for key, value in substatement_map.items()
            ]

        return match_table

    def for_all_substatements_attach_matches(self,
                                             match_table):
        attached_matches = []
        attached_matches.extend(match_table)
        return attached_matches

    @rpc
    def get_match_table_and_jsonld(self,
                                   job_description_id,
                                   framework_names,
                                   threshold):
        if not threshold:
            threshold = 0.44

        #web_pdb.set_trace()
        sentences_df = self.get_all_sentences(
            job_description_id)

        sentence_embeddings = self.get_all_sentence_embeddings(
            job_description_id,
            sentences_df)
                
        substatement_map = {}

        match_table =\
            self.for_all_frameworks_find_matches_and_store(
                job_description_id=job_description_id,
                substatement_map=substatement_map,
                sentences_df=sentences_df,
                sentence_embeddings=sentence_embeddings,
                framework_names=framework_names,
                threshold=threshold
            )

        return {
                    "matchTable": 
                                self.for_all_substatements_attach_matches(
                                    match_table
                                ),
                    "pipelineID": job_description_id,
                    "timestamp": str(datetime.datetime.utcnow())
                }
