"""
    quick script to get batch sentence encodings, train
    against what should be a nearly optimal linear model
    for reproducing
        "Sentence Similarity based on Semantic Nets and Corpus Statistics" by Li, et al.
    for a given parametrization (DELTA, etc.)
"""
import glob
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(format="%(levelname)s:%(message)s \t%(asctime)s",
                    level=logging.DEBUG,
                    datefmt="%m/%d/%Y %I:%M:%S %p")


class Config(object):
    logging.info("... setting up TensorFlow universal sentence encoder")
    #  see module caching: https://www.tensorflow.org/hub/basics
    module_url = "./tensorflow_models/universal_sentence_encoder/"
    embedding = hub.Module(module_url)
    data_directory = "./data"
    sentence_one_col = "ace_competency"
    sentence_two_col = "matched_competency"
    similarity_score_col = "similarity"
    repace_nan = ""

    embeddings_path = "./embeddings.npy"
    output_data = "./output.feather"

    #  initalize the tensor flow for USE graph
    graph = tf.Graph()
    with graph.as_default():
        # We will be feeding 1D tensors of text into the graph.
        text_input = tf.placeholder(
            dtype=tf.string,
            shape=[None])
        embed = hub.Module(module_url)
        embedded_text = embed(text_input)
        init_op = tf.group(
            [tf.global_variables_initializer(),
             tf.tables_initializer()])
    graph.finalize()

    session = tf.Session(graph=graph)
    session.run(init_op)
    #  see: https://github.com/tensorflow/hub/blob/master/docs/common_issues.md


def construct_data_frame(data_directory=None,
                         sentence_one_col=None,
                         sentence_two_col=None,
                         similarity_score_col=None,
                         replace_nan=None):
    ret = None
    df = pd.concat(
        map(
            lambda csv: pd.read_csv(csv, delimiter="\t"),
            glob.glob("./data/*.csv")
        )
    ).reset_index(drop=True)

    if {sentence_one_col, sentence_two_col, similarity_score_col} < set(df.columns):
        df.fillna(value=replace_nan, inplace=True)
        ret = df

    return ret


def construct_sentences(data_frame=None,
                        sentence_cols=["ace_competency",
                                       "matched_competency"]):
    return pd.Series(
        data_frame[sentence_cols].values.flatten()
    )


def batch_encode(sentences=None, config=Config):
    message_embeddings =\
        Config.session.run(
            Config.embedded_text,
            feed_dict={Config.text_input: sentences.values}
        )

    return message_embeddings


df = construct_data_frame(Config.data_directory,
                          Config.sentence_one_col,
                          Config.sentence_two_col,
                          Config.similarity_score_col,
                          replace_nan="")


if not Path(Config.embeddings_path).exists():
    logging.info("... batch encoding sentences")
    sentences = construct_sentences(df)
    logging.info('... About to batch encode {} sentences'.format(sentences))
    embeddings = batch_encode(sentences=sentences)
    logging.info('... About to write embeddings to disk...')
    np.save(Config.embeddings_path, embeddings)
else:
    embeddings = np.load(Config.embeddings_path)

if not Path(Config.output_data).exists():
    logging.info("... constructing dataframe")
    output = \
        pd.concat(
            (pd.DataFrame(embeddings.reshape((-1, 2*embeddings.shape[1]))),
             df[Config.similarity_score_col],
             df[Config.sentence_one_col],
             df[Config.sentence_two_col]),
            axis=1)
    # feather requires string column types
    output.columns = output.columns.astype(str)
    output.to_feather(Config.output_data)
