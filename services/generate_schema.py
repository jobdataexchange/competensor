from io import StringIO
import pandas as pd
from copy import deepcopy
from json import dumps
from datetime import datetime, timedelta
from nameko.rpc import rpc
from nameko.dependency_providers import Config
from nameko.extensions import DependencyProvider
from nameko_redis import Redis
from uuid import uuid5, NAMESPACE_DNS
from utils.selected_competency import filter_match_table_by_user_action
from utils.db import JDXDatabase
from utils.framework_similarity import FrameworkSimilarity
from utils.parser.clearinghouse import (
    read_excel_with_formatting,
    induce_tags
)
from uuid import uuid4, uuid5, NAMESPACE_URL


class GetPipeline(DependencyProvider):
    def __init__(self,
                 tablename=None,
                 uri=None):
        self.uri = uri
        self.tablename = tablename

    def setup(self):
        self.uri = self.uri or self.container.config['JDX_DB_URI']
        self.jdx_database = JDXDatabase(uri=self.uri)

    def get_dependency(self, worker_ctx):
        return self.jdx_database.get_pipeline_from_job_description


class GenerateSchema:
    name = "generate_schema"

    config = Config()
    client = Redis('match_table')
    get_pipeline = GetPipeline()

    csky_jsonld = {
        "@context": "http://jobdataexchange.org/jdxcontext.json",
        "@graph": [
            {
                "@id": "",
                "@type": "jdx:Organization",
                "schema:legalName": {"en-US": ""},
                "email": "",
                "url": "",
                "schema:address": {
                    "@type": "schema:PostalAddress",
                    # "schema:addressCountry": "",
                    # "schema:addressLocality": "",
                    # "schema:addressRegion": "",
                    # "schema:postalCode": "",
                    "schema:streetAddress": ""
                },
                # Drop location until we can parse geocoordinates
                # "schema:location": {
                #     "@type": "jdx:Place",
                #     "schema:geo": {
                #         "@type": "schema:GeoCoordinates",
                #         "latitude": None, # 13.1423,
                #         "longitude": None # 323.32423
                #     }
                # },
                "telephone": "",
                "schema:occupationalCategory": {
                    "@type": "AnnotatedDefinedTerm",
                    # "name": "",
                    # "description": {"en-US": ""},
                    "termCode": "",
                    # "inDefinedTermSet": ""
                },
                "jdx:industryCode": {
                    "@type": "AnnotatedDefinedTerm",
                    # "name": "",
                    # "description": {"en-US": ""},
                    "termCode": "",
                    # "inDefinedTermSet": ""
                },
                "hasJobPosting": "",
                "jdx:employerOverview": {"en-US": ""}
            },
            {
                "@id": "",
                "@type": "JobPosting",
                "schema:datePosted": "", #datetime ISO
                "schema:validThrough": "", # datetime ISO
                "totalJobOpenings": 0,
                "schema:title": {"en-US": ""},
                "schema:description": {"en-US": ""},
                "schema:industry": {"en-US": ""},
                "schema:occupationalCategory": {
                    "@type": "AnnotatedDefinedTerm",
                    # "name": "",
                    # "description": {"en-US": ""},
                    "termCode": "",
                    # "inDefinedTermSet": ""
                },
                "jdx:industryCode": {
                    "@type": "AnnotatedDefinedTerm",
                    # "name": "",
                    # "description": {"en-US": ""},
                    "termCode": "",
                    # "inDefinedTermSet": ""
                },
                "jdx:hiringOrganization": "",
                "jdx:employmentUnit": {
                    "@type": "Organization",
                    "name": ""
                },
                "jdx:positionID": "",
                "schema:jobLocationType": {"en-US": ""},
                # "schema:address": {
                #     "@type": "schema:PostalAddress",
                #     "schema:addressCountry": "",
                #     "schema:addressLocality": "",
                #     "schema:addressRegion": "",
                #     "schema:postalCode": "",
                #     "schema:streetAddress": ""
                # },
                # "schema:location": {
                #     "@type": "jdx:Place",
                #     "schema:geo": {
                #         "@type": "schema:GeoCoordinates",
                #         "latitude": None, # 13.1423,
                #         "longitude": None # 323.32423
                #     }
                # },
                "schema:jobLocation": {
                    # "@id": "", #TODO does this need an @id?
                    "@type": "schema:Place",
                    # "telephone": "",
                    # "name": "",
                    "address": {
                        "@type": "schema:PostalAddress",
                        # "schema:addressCountry": "",
                        # "schema:addressLocality": "",
                        # "schema:addressRegion": "",
                        # "schema:postalCode": "",
                        "schema:streetAddress": ""
                    }
                    # "faxNumber": "",
                    # "schema:geo": {
                    #     # "@id": "", #TODO (change to uuid)
                    #     "@type": "GeoCoordinates",
                    #     "latitude": "",
                    #     "longitude": "",
                    #     "name": ""
                    # }
                },
                "jdx:applicantLocationRequirement": {
                    # "@id": "", 
                    "@type": "schema:Place",
                    # "telephone": "",
                    "name": ""
                    # "address": {
                    #     "@type": "schema:PostalAddress",
                    #     "schema:addressCountry": "",
                    #     "schema:addressLocality": "",
                    #     "schema:addressRegion": "",
                    #     "schema:postalCode": "",
                    #     "schema:streetAddress": ""
                    # },
                    # "geo": {
                    #     "@id": "", # TODO (change to uuid)
                    #     "@type": "GeoCoordinates",
                    #     "latitude": None,
                    #     "longitude": None,
                    #     "name": ""
                    # }
                },
                "jdx:requiredAssessment": {
                    "@type": "AssessmentProfile",
                    "description": "" #why not name?
                },
                "jdx:jobTerm": {
                    "@type": "AnnotatedDefinedTerm",
                    "name": ""
                },
                "jdx:jobAgreement": {
                    "@type": "AnnotatedDefinedTerm",
                    "name": ""
                },
                "jdx:jobSchedule": {
                    "@type": "AnnotatedDefinedTerm",
                    "name": ""
                },
                "jdx:workHours": {
                    "@type": "AnnotatedDefinedTerm",
                    "name": ""
                },
                "schema:incentiveCompensation": {"en-US": ""},
                "schema:baseSalary": {
                    "@type": "schema:MonetaryAmount",
                    "schema:current": "USD",
                    "schema:minValue": None,
                    "schema:maxValue": None,
                    "payCycleInterval": {
                        "@type": "jdx:AnnotateDefinedTerm",
                        "name": {"en-US": ""}
                    },
                },
                "schema:jobBenefits": [],
                # "jdx:responsibilty": "",
                "jdx:requiredCredential": {
                    "@type": "Credential",
                    "description": {
                        "en-US": ""
                    }
                },
                "jdx:citizenshipRequirement": {
                    "@type": "AnnotatedDefinedTerm",
                    # "termCode": "USA",
                    "name": {
                        "en-US": ""
                    }
                },
                "jdx:physicalRequirement": {"en-US": ""},
                "jdx:sensoryRequirement": {"en-US": ""},
                "jdx:securityClearanceRequirement": {"en-US": ""},
                "jdx:specialCommitment": {"en-US": ""},
                "jdx:competency": [],
            }
        ]
    }


    def fill_in_job_schema_from_template(self, jsonld, pipeline):
        ORG = 0
        POSTING = 1
        graph = jsonld['@graph']
        
        def create_uuid_from_text(text):
            uuid = uuid5(NAMESPACE_URL, text)
            return uuid


        def create_new_resource(resource_uri, uuid=None):
            if uuid is None:
                uuid = str(uuid4())

            return f'{resource_uri}{uuid}'


        def create_new_jdx_resource():
            jdx_uri = "https://jobdataexchange.org/jdx/pp/resource/"
            return create_new_resource(jdx_uri)


        def create_new_jdx_known_competency_resource():
            jdx_competency_uri = "https://jobdataexchange.org/jdx/competency/"
            return create_new_resource(jdx_competency_uri)


        def create_new_jdx_custom_competency_resource(competency_text):
            jdx_custom_competency_uri = "https://jobdataexchange.org/jdx/competency/ug/"
            uuid = create_uuid_from_text(competency_text)
            return create_new_resource(jdx_custom_competency_uri, uuid)


        def create_new_unk_resource():
            unknown_uri = "https://placeholder.route/unknown/resource/"
            return create_new_resource(unknown_uri)


        # Generate IDs
        organization_uuid = create_new_jdx_resource()
        posting_uuid = create_new_jdx_resource()

        graph[ORG]['@id'] = organization_uuid
        graph[POSTING]['@id'] = posting_uuid

        graph[ORG]['hasJobPosting'] = posting_uuid
        graph[POSTING]['jdx:hiringOrganization'] = organization_uuid

        
        graph[ORG]['schema:legalName']['en-US'] =\
            pipeline.employer_name
        graph[ORG]['email'] =\
            pipeline.employer_email
        graph[ORG]['schema:address']['streetAddress'] =\
            pipeline.employer_address
        graph[ORG]['url'] =\
            pipeline.employer_website
        graph[ORG]['telephone'] =\
            pipeline.employer_phone   
        graph[ORG]['jdx:industryCode']['termCode'] =\
            pipeline.industry_code
        graph[ORG]['schema:occupationalCategory']['termCode'] =\
            pipeline.occupation_code
        graph[ORG]['jdx:employerOverview']['en-US'] =\
            pipeline.employer_overview

        graph[POSTING]['schema:title']['en-US'] =\
            pipeline.job_title

        def safely_convert_to_int_or_float(data):
            """ Takes a string or int and returns an int or None.
            """
            if data is None or data == "":
                return ""
            try:
                try:
                    return int(data)
                except ValueError:
                    return float(data)
            except ValueError:
                return str(data)

        job_openings_count = safely_convert_to_int_or_float(pipeline.job_openings)
        graph[POSTING]['totalJobOpenings'] = job_openings_count #schema
        graph[POSTING]['schema:datePosted'] = pipeline.date_posted
        graph[POSTING]['schema:validThrough'] = pipeline.valid_through
        
        graph[POSTING]['schema:description']['en-US'] =\
            pipeline.job_summary
        graph[POSTING]['schema:industry']['en-US'] =\
            pipeline.primary_economic_activity # should this be in the posting or the ORG?
        graph[POSTING]['jdx:industryCode']['termCode'] =\
            pipeline.industry_code
        graph[POSTING]['schema:occupationalCategory']['termCode'] =\
            pipeline.occupation_code

        graph[POSTING]["schema:jobLocation"]["address"]["schema:streetAddress"] =\
            pipeline.job_location        
        graph[POSTING]["schema:jobLocationType"]['en-US'] =\
            pipeline.job_location_type
        graph[POSTING]['jdx:employmentUnit']['name'] =\
            pipeline.employment_unit            
        graph[POSTING]['jdx:positionID'] =\
            pipeline.employer_identifier

        graph[POSTING]['jdx:requiredAssessment']["description"] =\
            pipeline.assessment

        graph[POSTING]['jdx:jobAgreement']['name'] =\
            pipeline.employment_agreement
        graph[POSTING]['jdx:jobTerm']['name'] =\
            pipeline.job_term
        graph[POSTING]['jdx:workHours']['name'] =\
            pipeline.work_hours
        graph[POSTING]['jdx:jobSchedule']['name'] =\
            pipeline.job_schedule

        graph[POSTING]['jdx:citizenshipRequirement']['name']['en-US'] =\
            pipeline.citizenship_requirement
        graph[POSTING]['jdx:physicalRequirement']['en-US'] =\
            pipeline.physical_requirement
        graph[POSTING]['jdx:sensoryRequirement']['en-US'] =\
            pipeline.sensory_requirement
        graph[POSTING]['jdx:securityClearanceRequirement']['en-US'] =\
            pipeline.security_clearance_requirement 
        graph[POSTING]['jdx:specialCommitment']['en-US'] =\
            pipeline.special_commitment
        
        minSalary = safely_convert_to_int_or_float(pipeline.minimum)
        maxSalary = safely_convert_to_int_or_float(pipeline.maximum)
        graph[POSTING]['schema:baseSalary']['schema:minValue'] =\
            minSalary
        graph[POSTING]['schema:baseSalary']['schema:maxValue'] =\
            maxSalary
        graph[POSTING]['schema:baseSalary']['payCycleInterval']['name']['en-US'] =\
            pipeline.frequency
        graph[POSTING]['schema:incentiveCompensation']['en-US'] =\
            pipeline.incentive_compensation

        graph[POSTING]['jdx:requiredCredential']['description']['en-US'] =\
            pipeline.requirements

        for a_benefit in pipeline.job_benefits:
            graph[POSTING]['schema:jobBenefits'].append(
                {
                    "@type": "jdx:AnnotateDefinedTerm",
                    "name": {"en-US": a_benefit}
                }
            )

        graph[POSTING]['jdx:applicantLocationRequirement']["name"] =\
            pipeline.application_location_requirement


        #  add in competencies
        print('going into fn')
        accepted_competencies, replaced_comeptencies =\
            filter_match_table_by_user_action(pipeline.pipeline_id, pipeline.match_table_selections)

        print('out of fn')
        for row in accepted_competencies.itertuples():
            print(row)
            graph[POSTING]["jdx:competency"].append(
                {
                    "@id": f'https://jobdataexchange.org/jdx/competency/{row.recommendationID}', # this should be a unique URI that encapsulates the competency data
                    "@type": "jdx:AnnotatedDefinedTerm",
                    # "jdx:annotatedTerm": "", # TODO this should link back to the canonical UUID for the framework competency URI?
                    # "termCode": "", # TODO what goes here?
                    "schema:description": {"en-US": row.framework_statement},
                    "schema:inDefinedTermSet": {
                        "@type": "DefinedTermSet",
                        "name": {
                            #"en-US": row.#framework_name, # framework name, eg "Cybersecurity Workforce Framework: Tasks (NICE)"
                            "url": f'https://jobdataexchange.org/jdx/framework/{row.frameworkID}' # this should be the canonical UUID for the framework URI
                        }
                    }
                    # "jdxmeta:recommendationUUID": row.recommendationID,
                    # "jdxmeta:substatement": row.substatement
                }
            )

        print('between for loops')
        for competency_text in replaced_comeptencies:
            print(competency_text)
            graph[POSTING]["jdx:competency"].append(
                {
                    "@id": create_new_jdx_custom_competency_resource(competency_text),
                    "@type": "jdx:AnnotatedDefinedTerm",
                    # "jdx:annotatedTerm": "",
                    "schema:description": {"en-US": competency_text},
                    "schema:inDefinedTermSet": {
                        "@type": "DefinedTermSet",
                        "name": {
                            "en-US": "User Generated Competency"
                        }
                    }
                    # "recommendationUUID": "",
                    # "jdxmeta:substatement": ""
                }
            )            

        return jsonld

    @rpc
    def generate_job_schema_file(self, pipeline_id):
        #  JDX Data Model note
        # 
        # The CSKy UI implicitly maps a flat property to a 
        # particular class and we have to implicitly store that property
        # in the class object that it belongs.
        #
        # However, in the general case, where anyoen is making a UI,
        # we won't know which class the user intends for a particular property.
        # The only way to handle that case is to require the user (UI maker) to
        # signal what class that property belongs to.
        #
        # An example of this is: `sensoryRequirement`, which belogns udner
        # JobMaster or JobPosting, as well as 2 other classes. We won't know which
        # unless the UI/user indicates.

        pipeline = self.get_pipeline(pipeline_id)

        job_schema_plus_file = self.fill_in_job_schema_from_template(
            deepcopy(self.csky_jsonld),
            pipeline
        )

        return job_schema_plus_file
