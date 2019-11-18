#!/bin/bash 
echo "... loading local tensorflow models ..."
cd /competensor
cd tensorflow_models/universal_sentence_encoder && tar xfz 2.tar.gz
echo "... loading small SpaCy model"
cd /competensor && tar xfz en_core_web_sm-2.1.0.tar.gz
echo "... setting up competensor ..."
cd /competensor
python build_competensor.py
echo "... starting services  ..."
cd /competensor
nameko run --config development.yaml services.hello:GreeterService services.frameworks:Frameworks competensor:Competensor services.previewer:Preview services.generate_schema:GenerateSchema
