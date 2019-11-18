""" Unit tests for competensor service  """
from unittest import TestCase
from unittest.mock import patch
from competensor import Competensor
import pandas as pd
from nameko.testing.services import worker_factory
from json import loads


class TestCompetensorServices(TestCase):
    def test_competensor_parsing_and_competency_extraction(self):
        """ Test comptensor Framework parsing and competency extraction
        """
        def mock_predict(similarities):
            return [0.75]*similarities.shape[0]

        mock_cybersecurity_framework =\
            """framework_statement,numeric_tag,uuid\nAttack stages,"section 4., row=961",5908761c-aead-592e-bf1d-49ad739c682a\nFootprinting and scanning,"section 4., row=962",78adab7a-91c1-5bdb-9a36-49bd957ff0c8\nEnumeration,"section 4., row=963",d88055e4-2636-5374-9e7f-129d0220add7\nGaining access,"section 4., row=964",7bc159f6-9e24-518d-9bfc-8e693bd6e172"""
        mock_job_description =\
            """The best software for the best price.\n\nJunior Developer\n\nDepartment: ITS - Division C\n\n123 Acme Way\nNew York, NY 11223\nwww.example.com\n\nSOC Code: 15-1132.00\nQuestions? Email info@example.com\nPosted on 4/2/2021 18:23:01\n\nInternal HRIS ID: #4567-363F\nACME is an equal opportunity employer\n\nShare this posting\n\n\n\n\n\nPosition:  Junior Developer (ITS - Division C)\n\nReporting Manager: Marigold D. Flower\n\nPosition Summary:\n\nAt ACME Corp. as a junior software developer youll have exciting opportunities to be a part of a small technical team of developers while directly impacting company success. The successful developer in this role will carry out software testing (BDD, JUnit, Spring, etc.) and develop software specified by a senior developer. This involves, but is not limited to, pair programming, working in a variety of programming languages, development tools as well as providing testing support. Provides Level 1+ & 2 support to production application environments. Must create code in conformance with ACMEs Development Standards and Guidelines.\n\nKey Responsibilities:\n\nWrites, maintain application code, database queries, scripts. Maintains web pages. Develop, execute unit tests.\n\nEstimate work progress and time to completion on projects.\n\nContinuous learning on corporate application development trends, ACME strategies and standards. Maintains ITS operating procedures and deployment strategies. \n\nCarry out code reviews, work in pair programming teams,  \n\nProvides planning and accurate time estimates for own assignments.\n\nConducts system, unit and integration testing. Handle regression testing.\n\nWork across multiple teams, excellent collaborator.\n\nMinimum Experience & Education Requirements\n\nBS Computer Science or equivalent,\n\nOR Associate Degree & 1 years of related job experience\n\nOR a 2 year IT certificate from an accredited institution & 3 years of related job experience\n\nOR a high school diploma or GED & 4 years hands on application development experience\n\n\n\nPreferred\n\nA degree related to information technology or computer science\n\nOracle, Java Framework experience and familiar with standard IDEs (Eclipse)\n\n\nOther Requirements\n\nExcellent analytical, problem solving skills.\n\nGood organizational skills and good oral/written presentation skills.\n\nKnowledge of SDP and other ACME IT development processes\n\nIn depth understanding of information technology industry, including emerging technologies, use cases, support services and the like. Expect to maintain and expand IT industry knowledge.\n\nAbility to be self directed.\n\n\n\nDisclaimer\n\nThe selected employee may engage in some or all combinations of the activities and responsibilities while also utilizing some or all of the competencies described above depending upon the role and department they are under. This job description describes the general nature and level of work and is not intended to be an all inclusive, or exhaustive list of responsibilities and competencies required. This job description does not limit the right of supervisors or management to direct, assign or control the work of employees under their supervision."""
        mock_job_description_sentences =\
            """substatement,jdx_property_a,substatementID,jdx_class_a,jdx_class_b,jdx_property_b,jdx_class_c,jdx_property_c\nAttack stages,competency,5908761c-aead-592e-bf1d-49ad739c682a,,,,,\nFootprinting and scanning,,78adab7a-91c1-5bdb-9a36-49bd957ff0c8,,,,,\nEnumeration,competency,d88055e4-2636-5374-9e7f-129d0220add7,,,,,\nGaining access,,7bc159f6-9e24-518d-9bfc-8e693bd6e172,,,,,competency\n"""

        mock_framework_embeddings =\
            pd.read_csv("./tests/fixtures/embeddings/embeddings.csv")\
              .to_csv(index=False)
        mock_sentence_embeddings =\
            pd.read_csv("./tests/fixtures/embeddings/embeddings.csv")\
              .iloc[:, :-1]\
              .values + 0.13
        mock_jsonld =\
            loads(
                """
                {
                    "@context": "http://jobdataexchange.org/jdxcontext.json",
                    "@graph": [
                        {
                        "@id": "https://acme.corp",
                        "@type": "jdx:Organization",
                        "schema:legalName": {"en-US": "ACME"} ,
                        "jdx:hasJobPosting": "http://Acme.com/jobPostings/5678-90DA",
                        "schema:address": {
                                "@type": "schema:PostalAddress",
                                "schema:addressCountry": "US",
                                "schema:addressLocality": "New York",
                                "schema:addressRegion": "NY",
                                "schema:postalCode": "11223",
                                "schema:streetAddress": "123 Acme Way"
                            }
                        }
                    ]
                }
                """
            )

        with patch('joblib.load', side_effect=lambda x: x):
            competensor = worker_factory(Competensor)

            competensor.model\
                       .predict\
                       .side_effect = mock_predict
            competensor.universal_sentence_encoder\
                       .embed\
                       .return_value = mock_sentence_embeddings
            competensor.components\
                       .decompose\
                       .return_value = mock_job_description_sentences
            competensor.frameworks\
                       .get\
                       .return_value = mock_cybersecurity_framework
            competensor.embeddings\
                       .get\
                       .return_value = mock_framework_embeddings
            competensor.get_raw_text\
                       .get_raw_text_from_pipeline\
                       .return_value = mock_job_description
            competensor.get_raw_text\
                       .get_context_object\
                       .return_value = mock_jsonld

            match_table =\
                competensor.get_match_table_and_jsonld(
                    'fake jobdescription id',
                    'Clearing House Cybersecurity')

            assert len(match_table["match_table"]) == 2
            assert len(
                match_table["jsonld"]["@graph"][0]["jdx:competency"]
                ) == 2
