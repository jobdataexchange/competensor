# FROM brighthivestage/competensor_base:latest
# FROM brighthivestage/competensor_base_with_data:latest
FROM python:3.6.8
WORKDIR /competensor
RUN wget https://jdx-data-model.s3.us-east-2.amazonaws.com/linear_5_19.joblib
RUN wget https://jdx-data-model.s3.us-east-2.amazonaws.com/2.tar.gz -P tensorflow_models/universal_sentence_encoder/
RUN wget https://jdx-data-model.s3.us-east-2.amazonaws.com/en_core_web_sm-2.1.0.tar.gz
RUN apt-get update
RUN apt-get install -y libpq-dev python-dev build-essential swig wget
RUN pip install pipenv
RUN pip install numpy
RUN pip install auto-sklearn
RUN pip install spacy
# competensor_base above
ADD Pipfile Pipfile
ADD Pipfile.lock Pipfile.lock
RUN pipenv install --system
ADD LICENSE LICENSE
ADD clients clients
ADD config config
ADD development.yaml development.yaml
ADD speedup speedup
ADD utils utils
ADD README.md README.md
ADD competensor.py competensor.py
ADD datastore datastore
ADD services services
ADD tests tests
ADD frameworks frameworks
ADD tensorflow_models tensorflow_models
ADD run.sh run.sh
ADD build_cmd.py build_cmd.py
ADD build_competensor.py build_competensor.py
RUN chmod a+x run.sh
ADD models models
ENTRYPOINT ["/competensor/run.sh"]
