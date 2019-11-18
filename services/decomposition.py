import pandas as pd
from uuid import uuid5, NAMESPACE_DNS
from nameko.rpc import rpc, RpcProxy
from nameko.extensions import DependencyProvider
from spacy.lang.en import English


class Sentencizer:
    def __init__(self):
        self.nlp = English()
        sentencizer = self.nlp.create_pipe("sentencizer")
        self.nlp.add_pipe(sentencizer)

    def decompose(self, raw_text):
        sentences = list(
            self.nlp(raw_text)
                .sents)
        number_of_sentences = len(sentences)
        return pd.DataFrame(
            {
                "substatement": sentences,
                "substatementID":
                    [str(uuid5(NAMESPACE_DNS, sentence.text.strip())) for sentence in sentences],
                "jdx_class_a": ""*number_of_sentences,
                "jdx_property_a": "competency",
                "jdx_class_b": ""*number_of_sentences,
                "jdx_property_b": ""*number_of_sentences,
                "jdx_class_c": ""*number_of_sentences,
                "jdx_property_c": ""*number_of_sentences,
            }
        ).to_csv(index=False)


class Decomposer(DependencyProvider):
    def get_dependency(self, worker_ctx):
        return Sentencizer()


class GetRawText(DependencyProvider):
    def __init__(self,
                 tablename=None,
                 uri=None):
        self.uri = uri
        self.tablename = tablename
        self.jdx_database = None

    def setup(self):
        self.uri = self.uri or self.container.config('JDX_DB_URI')

    def get_dependency(self, worker_ctx):
        return self.jdx_database.get_raw_text_from_pipeline


class DecomposeJobDescription:
    name = "decompose_raw_job_description"
    get_raw_text = GetRawText()
    decomposer = Decomposer()

    @rpc
    def decompose(self, job_description_id):
        return self.decomposer.decompose(
            self.get_raw_text(job_description_id)
        )
