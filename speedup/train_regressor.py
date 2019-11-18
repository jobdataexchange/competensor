"""
    train_regressor.py

    Current state of the art (SOTA) NLP approaches provide generic embeddings with 
    the  intent that they can be applied to down stream specific tasks.
    Here we use the universal sentence encoder embedings since their
    inner product gives SOTA results on sentence textual similarity (STS)

    There are many criticism of 'fine tuning' embeddings, which can be found here:

    https://www.reddit.com/r/MachineLearning/comments/84r7ws/d_to_fine_tune_word_embeddings_or_not/
    https://github.com/google-research/bert/issues/276
    https://github.com/tensorflow/hub/blob/master/docs/fine_tuning.md

    These criticism are especially valid when applied to tasks involving restricted vocabulary
    (like frameworks written at the college level or against specific domain language), 
    or where a set of words won't be found.

    For that reason, the easiest next step is to just train a regressor on the embeddings
    and original Competensor similarity scores to approximate it under a SOTA STS representation

    references:
        "Sentence Similarity based on Semantic Nets and Corpus Statistics" by Li, et al.

        @article{DBLP:journals/corr/abs-1803-11175,
        author    = {Daniel Cer and
                    Yinfei Yang and
                    Sheng{-}yi Kong and
                    Nan Hua and
                    Nicole Limtiaco and
                    Rhomni St. John and
                    Noah Constant and
                    Mario Guajardo{-}Cespedes and
                    Steve Yuan and
                    Chris Tar and
                    Yun{-}Hsuan Sung and
                    Brian Strope and
                    Ray Kurzweil},
        title     = {Universal Sentence Encoder},
        journal   = {CoRR},
        volume    = {abs/1803.11175},
        year      = {2018},
        url       = {http://arxiv.org/abs/1803.11175},
        archivePrefix = {arXiv},
        eprint    = {1803.11175},
        timestamp = {Mon, 13 Aug 2018 16:46:40 +0200},
        biburl    = {https://dblp.org/rec/bib/journals/corr/abs-1803-11175},
        bibsource = {dblp computer science bibliography, https://dblp.org}
        }
"""
import sklearn.metrics
import sklearn.model_selection
import autosklearn.regression
from autosklearn.metrics import mean_squared_error
import pandas as pd
import numpy as np
from joblib import dump, load


class Config(object):
    training_data_path = "./output.feather"
    training_data = pd.read_feather(training_data_path)
    do_full_dataframe = False
    do_inner_product = False
    do_small_ensemble = False
    do_one_ensemble = True


X_train, X_test, y_train, y_test = \
    sklearn.model_selection.train_test_split(
        Config.training_data.iloc[:, :-3],
        Config.training_data["similarity"],
        random_state=1)

automl = autosklearn.regression.AutoSklearnRegressor(
    time_left_for_this_task=3600,
    per_run_time_limit=360,
    tmp_folder="./tmp/",
    output_folder="./out",
    ml_memory_limit=30720,
    ensemble_memory_limit=3072,
    n_jobs=6
)


if Config.do_inner_product:
    print("\t... running inner product training")
    # we need to preprocess X_train into inner products
    # see if (X * X_.sum() is faster?
    X_train_inner_product =\
        np.sum(
            np.multiply(X_train.values[:, :512], X_train.values[:, 512:]),
            axis=1
        )

    automl.fit(X_train_inner_product.reshape(-1,1),
               y_train,
               metric=mean_squared_error,
               dataset_name="inner_product_dataframe_ace_similarities")
    dump(automl, 'automl_inner_product_dataframe.joblib')

    print(automl.show_models())
    print(automl.sprint_statistics())

    X_test_inner_product =\
        np.sum(
            np.multiply(X_test.values[:, :512], X_test.values[:, 512:]),
            axis=1
        )
    predictions = automl.predict(X_test_inner_product)
    print("R2 score:", sklearn.metrics.r2_score(y_test, predictions))
    print("MSE:", sklearn.metrics.mean_squared_error(y_test, predictions))


if Config.do_small_ensemble:
    print("\t... running small ensemble")
    small_automl = autosklearn.regression.AutoSklearnRegressor(
        time_left_for_this_task=3600,
        per_run_time_limit=360,
        tmp_folder="./tmp_small/",
        output_folder="./out_small/",
        ml_memory_limit=30720,
        ensemble_memory_limit=3072,
        n_jobs=6,
        ensemble_nbest=3
    )

    # we need to preprocess X_train into inner products
    X_train_inner_product =\
        np.sum(
            np.multiply(X_train.values[:, :512], X_train.values[:, 512:]),
            axis=1
        )

    small_automl.fit(X_train_inner_product.reshape(-1,1),
                     y_train,
                     metric=mean_squared_error,
                     dataset_name="inner_product_dataframe_ace_similarities")
    dump(small_automl, 'automl_small_inner_product_dataframe.joblib')

    print(small_automl.show_models())
    print(small_automl.sprint_statistics())

    X_test_inner_product =\
        np.sum(
            np.multiply(X_test.values[:, :512], X_test.values[:, 512:]),
            axis=1
        )

    predictions = small_automl.predict(
        X_test_inner_product.reshape(-1, 1)
        )
    print("R2 score:", sklearn.metrics.r2_score(y_test, predictions))
    print("MSE:", sklearn.metrics.mean_squared_error(y_test, predictions))


if Config.do_one_ensemble:
    print("\t... running one ensemble")
    one_automl = autosklearn.regression.AutoSklearnRegressor(
        time_left_for_this_task=3600,
        per_run_time_limit=360,
        tmp_folder="./tmp_one/",
        output_folder="./out_one/",
        ml_memory_limit=30720,
        ensemble_memory_limit=3072,
        n_jobs=6,
        ensemble_nbest=1
    )

    # we need to preprocess X_train into inner products
    X_train_inner_product =\
        np.sum(
            np.multiply(X_train.values[:, :512], X_train.values[:, 512:]),
            axis=1
        )

    one_automl.fit(X_train_inner_product.reshape(-1, 1),
                   y_train,
                   metric=mean_squared_error,
                   dataset_name="inner_product_dataframe_ace_similarities")
    dump(one_automl, 'automl_one_inner_product_dataframe.joblib')

    print(one_automl.show_models())
    print(one_automl.sprint_statistics())

    # we need to preprocess X_train into inner products
    X_test_inner_product =\
        np.sum(
            np.multiply(X_test.values[:, :512], X_test.values[:, 512:]),
            axis=1
        )

    predictions = one_automl.predict(
        X_test_inner_product.reshape(-1, 1)
        )
    print("R2 score:", sklearn.metrics.r2_score(y_test, predictions))
    print("MSE:", sklearn.metrics.mean_squared_error(y_test, predictions))

if Config.do_full_dataframe:
    print("\t... running full dataframe training")    
    automl.fit(X_train,
               y_train,
               metric=mean_squared_error,
               dataset_name="full_dataframe_ace_similarities")
    dump(automl, 'automl_full_dataframe.joblib')

    print(automl.show_models())
    print(automl.sprint_statistics())

    predictions = automl.predict(X_test)
    print("R2 score:", sklearn.metrics.r2_score(y_test, predictions))
    print("MSE:", sklearn.metrics.mean_squared_error(y_test, predictions))
