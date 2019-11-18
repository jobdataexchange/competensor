import pandas as pd
from redis import Redis
from yaml import full_load
from io import StringIO

with open('./development.yaml', 'r') as stream:
    config = full_load(stream)

match_table = Redis.from_url(config['REDIS_URIS']['match_table'],
                             decode_responses=True)

match_table_header = [
        "substatementID",
        "recommendationID",
        "framework_statement",
        "frameworkID",
        "numeric_tag",
        "value",
        "substatement",
        "embedding_index"]


def get_matches(pipeline_id):
    matches = pd.read_csv(
        StringIO(
            match_table.get(
                pipeline_id)
            ),
        names=match_table_header
    )
    return matches


def get_accepted_and_replaced_competencies(matches, user_actions_from_jdx_api):
    accepted_competencies = set()
    replaced_competencies = set()

    for a_selection in user_actions_from_jdx_api:
        if 'accept' in a_selection:
            accepted_competencies.update(
                [a_selection['accept']['recommendationID']]
            )
        if 'replace' in a_selection:
            replaced_competencies.update(
                [a_selection['replace']['name']]
            )

    print(f'accepted: {accepted_competencies}')
    print(f'replaced: {replaced_competencies}')
    rows_that_were_accepted = matches["recommendationID"].isin(accepted_competencies)
    print(f'rows_that_were_accepted: {rows_that_were_accepted}')

    return matches[rows_that_were_accepted], replaced_competencies


# work function
def filter_match_table_by_user_action(pipeline_id, user_actions_from_jdx_api):
    """
    user_actions_from_jdx_api = [
        {
            "substatementID": "27690469-b981-510a-9f59-0b19e618c553",
            "accept": {
                "recommendationID": "f1f4dee1-29d8-5a4c-b4c6-969f93a9ffc1"
            }
        },
        {
            "substatementID": "76631a42-878f-52e6-8327-ff93457a0ab4"
        },
        {
            "substatementID": "7a1fa7ad-460e-53ca-a577-3860e40dfba5",
            "replace": {
                "name": "hello world"
            }
        }
    ]
    """

    matches = get_matches(pipeline_id)

    accepted_competencies, replaced_competencies = get_accepted_and_replaced_competencies(matches, user_actions_from_jdx_api)
    
    print(accepted_competencies)
    # print(replaced_competencies)
    return accepted_competencies, replaced_competencies
