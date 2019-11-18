import pandas as pd
from io import StringIO
from pathlib import Path
from uuid import uuid5
from redis import Redis
from utils.frameworks import parse_and_write_framework
from utils.embeddings import UniversalSentenceEncoder
from yaml import full_load


class NULL_NAMESPACE:
    bytes = b''


class BuildCompetensorFrameworks():
    
    with open('./development.yaml', 'r') as stream:
        config = full_load(stream)

    check_frameworks = config['check_if_framework_exists_on_build_competensor']

    frameworks_client = Redis.from_url(config['REDIS_URIS']['frameworks'], decode_responses=True)
    embeddings_client = Redis.from_url(config['REDIS_URIS']['embeddings'], decode_responses=True)
    universal_sentence_encoder = UniversalSentenceEncoder()

    def with_providers_and_store_frameworks(self):
        for directory in self.config['frameworks']['directories']:
            for file_path in Path(directory).glob("*.yaml"):
                print(file_path)
                with open(file_path, 'r') as stream:
                    framework = full_load(stream)

                    if self.check_frameworks:
                        if self.frameworks_client.exists(framework['framework_id']):
                            print('found file, skipping it')
                            continue

                    self.frameworks_client.set(
                        framework['framework_id'],
                        parse_and_write_framework(
                            provider=framework['provider'],
                            path=framework['source_path']
                            )
                        )

    def construct_sentences(self,
                            data_frame=None,
                            sentence_cols=["framework_statement"]):
        return pd.Series(
            data_frame[sentence_cols].values.flatten()
        )

    def and_convert_frameworks_to_embeddings(self):
        for framework in self.frameworks_client.keys():

            if self.check_frameworks:
                if self.embeddings_client.exists(framework):
                    continue

            framework_df = pd.read_csv(
                StringIO(
                    self.frameworks_client.get(
                        framework))
            )

            if framework_df.empty:
                print("*****\t WARNING (build_competensor, embeddings): ", framework)
                print("*****\t ", framework_df)

            if not framework_df.empty:
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
                self.embeddings_client.set(framework, df.to_csv(index=False))            


if __name__ == "__main__":
    print("\t ... about to initalize BuildCompetensorFrameworks")
    build_competensor = BuildCompetensorFrameworks()
    print("\t ... about to store frameworks with providers")
    build_competensor.with_providers_and_store_frameworks()
    print("\t ... about to convert frameworks to universal sentence encoder embeddings")
    build_competensor.and_convert_frameworks_to_embeddings()
