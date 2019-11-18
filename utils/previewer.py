"""
    previewer.py

    For a given relational data model or taxonomy, we want to
    label chunks of text in aggregate for quick human review, e.g.
"""

from unittest.mock import Mock
#from utils.embeddings import UniversalSentenceEncoder
import spacy
import numpy as np
import seaborn
import os
from pathlib import Path
import re
import regex

nlp = spacy.load("./en_core_web_sm-2.1.0/en_core_web_sm/en_core_web_sm-2.1.0/")
os.environ["TFHUB_CACHE_DIR"] = "./tensorflow_models/"
module_url = "https://tfhub.dev/google/universal-sentence-encoder/2"     
paragraph_regex = re.compile("(^.*:.*)(\n^.*)", re.M)

title_regex = re.compile("(?:.*[:|-]\s)\s((?:\w+\s)+)(?:\W)")


def yield_paragraphs(job_description, regex=paragraph_regex):
    return regex.finditer(job_description)


def get_spacy_ner_and_entities(text):
    ner_and_entities = {}
    doc = nlp(text)
    for token in doc:
        if token.like_email:
            ner_and_entities['like_email'] =\
                ner_and_entities.get('like_email', 0) + 1
        if token.like_url:
            ner_and_entities['like_url'] =\
                ner_and_entities.get('like_url', 0) + 1
        if token.like_num:
            ner_and_entities['like_num'] =\
                ner_and_entities.get('like_num', 0) + 1

        sentiment = ner_and_entities.get('sentiment', 0)
        if token.sentiment > sentiment:
            ner_and_entities['sentiment'] = token.sentiment

        ner_and_entities[token.ent_type_] =\
            ner_and_entities.get(token.ent_type_, 0) + 1

        ner_and_entities[token.pos_] =\
            ner_and_entities.get(token.pos_, 0) + 1

    return ner_and_entities

jobMaster = set()

organization = \
    {
        "Organization": set(),
        "possible_parent_properities": set()
    }


def title(text,
          ner_and_entities=None,
          jobMaster=jobMaster):
    if 'Position' in text or\
       'Title' in text or\
       'Role' in text:
        if len(re.findall(title_regex, text)) > 0:
            jobMaster.add("title")

    return jobMaster


def employerOverview(text,
                     jobMaster=jobMaster,
                     ner_and_entities=None):
    if not ner_and_entities:
        ner_and_entities = get_spacy_ner_and_entities(text)

    if 'sentiment' in ner_and_entities and \
        ner_and_entities['sentiment'] > 0.3:
        # assume they're excitedly talking about themselves or the job applicant
        # might need a larger model than web sm to get sentiment
        jobMaster.add("employerOverview")

    #  note: this is a bit zealous, should take out
    if 'summary' in text or \
       'Summary:' in text or \
       'summary:' in text or \
       'about us' in text or \
       'About Us' in text or \
       'About us' in text:
        jobMaster.add("employerOverview")

    return jobMaster


def qualificationSummary(text,
                         jobMaster=jobMaster,
                         ner_and_entities=None):
    if not ner_and_entities:
        ner_and_entities = get_spacy_ner_and_entities(text)

    # note: should bootstrap a dictionary of synoymns to check
    if 'qualification' in text or\
       'qualified' in text or \
       'expertise' in text or \
       'proficiency' in text or \
       'competency' in text or \
       'mastery' in text:
        jobMaster.add("qualificationSummary")

    return jobMaster


def competencies(text,
                 jobMaster=jobMaster,
                 ner_and_entities=None):
    if not ner_and_entities:
        ner_and_entities = get_spacy_ner_and_entities(text)

    if (ner_and_entities.get('ORG', 0) + ner_and_entities.get('VERB', 0)) /\
        ner_and_entities.get('NOUN', 100) > 0.4:
        jobMaster.add("competency")
    
    if 'skills' in text or \
       'Skills' in text or \
       'Knowledge' in text or \
       'knowledge' in text or \
       'abilit' in text or \
       'Abilit' in text:
        jobMaster.add("competency")

    return jobMaster


def experience_education_credential(text,
                                    jobMaster=jobMaster,
                                    ner_and_entities=None):
    if "education" in text or "Education" in text or\
       "Degree" in text or "degree" in text or \
        "Masters" in text or "PhD" in text or \
        "Ph.D" in text:
        jobMaster.add("education")

    if "experience" in text or "Experience" in text:
        jobMaster.add("experience")

    if "credential" in text or "Credential" in text:
        jobMaster.add("credential")

    return jobMaster


def condition(text,
              jobMaster=jobMaster,
              ner_and_entities=None):
    if not ner_and_entities:
        ner_and_entities = get_spacy_ner_and_entities(text)

    no_verbs = ner_and_entities.get("VERB", 0)*0.3
    dates = ner_and_entities.get("DATE", 0)
    cconj = ner_and_entities.get("CCONJ", 0)
    if (cconj + dates + no_verbs) / ner_and_entities[''] > 0.4:
        jobMaster.add("requiredCondition")
        jobMaster.add("preferredCondition")

    return jobMaster


def responsbilities(text,
                    jobMaster=jobMaster,
                    ner_and_entities=None):
    if not ner_and_entities:
        ner_and_entities = get_spacy_ner_and_entities(text)

    if ((ner_and_entities.get('ORG', 0) +
         ner_and_entities.get('VERB', 0) +
         ner_and_entities.get('PUNCT', 0)) / ner_and_entities['']) > 0.75:
        jobMaster.add("responsibilities")

    if 'Responsibilities' in text or \
       'responsibilties' in text or \
       'duties' in text or \
       'Duties' in text:
        jobMaster.add("responsibilities")


    return jobMaster


def reporting(text,
              ner_and_entities=None,
              jobMaster=jobMaster):
    if 'reporting' in text or\
       'Reporting' in text or\
       'reports' in text:
        jobMaster.add("reportingRelationship")

    return jobMaster


def disclaimer(text,
               ner_and_entities=None,
               jobMaster=jobMaster):
    if 'disclaimer' in text or\
       'Disclaimer' in text or\
       'not intended to be' in text or\
       'exhaustive list' in text:
        jobMaster.add("disclaimer")

    return jobMaster


def address_url_email_org(text,
                          organization=organization,
                          ner_and_entities=None):
    if not ner_and_entities:
        ner_and_entities = get_spacy_ner_and_entities(text)

    if ner_and_entities.get("CARDINAL", 0) > 1 and \
       ner_and_entities.get("GPE", 0)      > 1 and \
       ner_and_entities.get("ORG", 0)      > 0:
        organization.add("address")

    if ner_and_entities.get("like_email", 0) > 0:
        # just going to make an assumption here, if email present, then hiring
        organization.add("hiringOrganization")
        organization.add("email")

    #  not for 6.24 demo
    # if "possible_parent_properities" not in organization:
    #     organization["possible_parent_properities"] = set()
    # if 'posted by' in text or \
    #    'behalf of' in text:
    #     organization["possible_parent_properities"].add("postingRequestor")
    # if 'subsidiary' in text or \
    #    'Subsidiary' in text:
    #     organization["possible_parent_properities"].add("employmentUnit")

    return organization


def yield_paragraphs_v2(text):
    last_span = 0 
    prior_line_lengths = [] 
    for match in regex.finditer('(?P<previous>^.*)\n(?P<current>^.*)\n(?P<next>^.*)\n?',
                                text,
                                overlapped=True,
                                flags=regex.MULTILINE):
        previous_length = match.span(1)[1] - match.span(1)[0] + 0.01
        current_length = match.span(2)[1] - match.span(2)[0] + 0.01
        next_length = match.span(3)[1] - match.span(3)[0] + 0.01

        if current_length > 0.01:
            prior_line_lengths.append(previous_length)
        if previous_length/current_length > 1.6 and \
           next_length/current_length > 1.6:
            #yield text[last_span:match.span(1)[1]]
            yield text[last_span:match.span(1)[1]]
            last_span = match.span(2)[0]
            prior_line_lengths = []

            # print("\n *******",
            #       text[last_span:match.span(1)[1]],
            #       "\n **********")

            # print("\n average line length {}, next length {}".format(
            #     sum(prior_line_lengths)/len(prior_line_lengths),
            #     next_length))

            # current_line_entites = get_spacy_ner_and_entities(
            #     match.group("previous")
            # )
            # paragraph_entites = get_spacy_ner_and_entities(
            #     text[last_span:match.span(1)[1]]
            # )

            # print("\n current entites", current_line_entites)
            # print("\n paragraph entites \n", paragraph_entites)

    #  get remaining content
    if len(text) > match.span(1)[1]:
        yield text[last_span:]
