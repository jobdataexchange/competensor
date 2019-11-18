from nameko.rpc import rpc
from nameko.extensions import DependencyProvider
from utils.db import JDXDatabase
from utils.previewer import (
    yield_paragraphs_v2,
    get_spacy_ner_and_entities,
    title,
    employerOverview,
    qualificationSummary,
    competencies,
    experience_education_credential,
    condition,
    responsbilities,
    reporting,
    disclaimer,
    address_url_email_org,
)


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
        return self.jdx_database.get_raw_text_from_pipeline


class Preview:
    name = "previewer"
    get_raw_text = GetRawText()

    @rpc
    def preview(self, job_description_id=None, text=None):
        if not text:
            text = self.get_raw_text(job_description_id)

        the_paragraphs = []
        fields = []
        for paragraph_number, match in enumerate(yield_paragraphs_v2(text)):
            paragraph = match  #match.group()
            ner_and_entites = get_spacy_ner_and_entities(paragraph)

            the_paragraphs.append(paragraph)

            organization = set()
            organization =\
                address_url_email_org(paragraph,
                                      organization=organization,
                                      ner_and_entities=ner_and_entites)
            if len(organization) > 0:
                if 'address' in organization:
                    fields.append(
                        {
                            "field": "Organization.address",
                            "paragraph_number": paragraph_number
                        }
                    )
                if 'email' in organization:
                    fields.append(
                        {
                            "field": "Organization.email",
                            "paragraph_number": paragraph_number
                        }
                    )                    
                if 'hiringOrganization' in organization:
                    fields.append(
                        {
                            "field": "hiringOrganization",
                            "paragraph_number": paragraph_number
                        }
                    )                    
          
            for job_master_func in [title, employerOverview, qualificationSummary,
                                    competencies, experience_education_credential, condition,
                                    responsbilities, reporting, disclaimer]:
                jobMaster = set()                                    
                jobMaster = job_master_func(paragraph,
                                            jobMaster=jobMaster,
                                            ner_and_entities=ner_and_entites)

                for key in jobMaster:
                    fields.append(
                        {
                            "field": key,
                            "paragraph_number": paragraph_number
                        }
                    )

        return {
            "paragraphs": the_paragraphs,
            "fields": fields
            }
