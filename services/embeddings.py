from io import StringIO
import pandas as pd
from nameko_redis import Redis
from nameko.rpc import rpc, RpcProxy
from uuid import uuid5
from utils.embeddings import UniversalSentenceEncoder


class NULL_NAMESPACE:
    bytes = b''


class Embeddings:
    name = "embeddings"
    client = Redis('embeddings')
    framework_rpc = RpcProxy("frameworks")

    def __init__(self,
                 module_url="./tensorflow_models/universal_sentence_encoder/",
                 encoder_type="DAN"):
        self.universal_sentence_encoder = UniversalSentenceEncoder(
            module_url=module_url,
            encoder_type=encoder_type
        )

    def construct_sentences(self,
                            data_frame=None,
                            sentence_cols=["value"]):
        return pd.Series(
            data_frame[sentence_cols].values.flatten()
        )

    @rpc
    def generate_and_write_framework_embeddings(self,
                                                framework_name):
        framework_df = pd.read_csv(
            StringIO(
                self.framework_rpc.get_framework(
                    framework_name).decode("utf-8"))
        )
        embeddings = self.universal_sentence_encoder\
                         .embed(
                             sentences=self.construct_sentences(
                                 framework_df)
                         )
        df = pd.DataFrame(embeddings.reshape(
                            (-1, embeddings.shape[1])))
        df["uuids"] = df.apply(
            lambda row: uuid5(NULL_NAMESPACE, str(row.values)),
            axis=1)

        self.client.set(framework_name, df.to_csv(index=False))
