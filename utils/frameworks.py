import yaml
import pandas as pd
from uuid import uuid5, NAMESPACE_DNS
from utils.parser.clearinghouse import (
    read_excel_with_formatting,
    induce_tags
)
from utils.parser.aarc import \
    break_into_alphanumeric_columns_and_forward_fill
from utils.parser.surgical_board import \
    get_series
from utils.parser.nbrc import \
    get_series as nbrc_get_series
from utils.parser.ctdl_to_simple import read_jsonld_and_parse


def ctdl(file_path):
    return read_jsonld_and_parse(file_path)

def clearinghouse(provider_args, path):
    df = read_excel_with_formatting(
            path,
            sheet_name=provider_args["sheet_name"],
            competency_col=provider_args["competency_col"],
            skiprows=provider_args["skiprows"])
    df = induce_tags(df)
    df["uuid"] = df.value.apply(
        lambda value: uuid5(NAMESPACE_DNS, value))
    df.rename(axis="columns",
              mapper={
                    "value": "framework_statement",
                    "tags": "numeric_tag"},
              inplace=True)
    df = df[["framework_statement",
             "uuid",
             "numeric_tag"]]

    return df.to_csv(index=False)


def parse_and_write_framework(path,
                              provider='clearinghouse',
                              provider_args=None):
    if 'clearinghouse' == provider:
        return clearinghouse(provider_args, path)

    if 'clearinghouse_skip_5_col_2' == provider:
        provider_args = {
            "sheet_name": "Sheet1",
            "competency_col":2,
            "skiprows":5
            }
        return clearinghouse(provider_args, path)

    if 'clearinghouse_skip_5_col_0' == provider:
        provider_args = {
            "sheet_name": "Sheet1",
            "competency_col":0,
            "skiprows":5
            }
        return clearinghouse(provider_args, path)
                
    if 'ltcss' == provider:
        if not provider_args:
            provider_args = {
                "sheet_name": "Sheet1",
                "competency_col":2,
                "skiprows":5
                }
        return clearinghouse(provider_args, path)

    if 'automation' == provider or\
       'energy' == provider:
        if not provider_args:
            provider_args = {
                "sheet_name": "Sheet1",
                "competency_col":2,
                "skiprows":5
                }
        return clearinghouse(provider_args, path)

    if 'retail' == provider or 'commerical' == provider:
        if not provider_args:
            provider_args = {
                "sheet_name": "Sheet1",
                "competency_col":0,
                "skiprows":5
                }
        return clearinghouse(provider_args, path)

    if 'aarc' == provider:
        df = break_into_alphanumeric_columns_and_forward_fill(
            file_path=path
        )
        df['numeric_tag'] =\
            df.agg(
                lambda row: 
                    f"{row['area']} {row['uppercase']} {row['numbers']} {row['lowercase']}".replace("nan",""), axis=1)
        df["uuid"] = df.text.apply(
            lambda value: uuid5(NAMESPACE_DNS, value))            
        df.rename(axis="columns",
                  mapper={"text": "framework_statement"},
                  inplace=True)
        df = df[["framework_statement",
                 "uuid",
                 "numeric_tag"]]

        return df.to_csv(index=False)

    if 'surgical_board' == provider:
        df = get_series(
            file_path=path
        )
        df['numeric_tag'] =\
            df.agg(
                lambda row: 
                    f"{row['roman']} {row['uppercase']} {row['lowercase']}".replace("nan",""), axis=1)
        df["uuid"] = df.text.apply(
            lambda value: uuid5(NAMESPACE_DNS, value))            
        df.rename(axis="columns",
                  mapper={"text": "framework_statement"},
                  inplace=True)
        df = df[["framework_statement",
                 "uuid",
                 "numeric_tag"]]

        return df.to_csv(index=False)        

    if 'nbrc' == provider:
        df = nbrc_get_series(
            file_path=path
        )
        df['numeric_tag'] =\
            df.agg(
                lambda row: 
                    f"{row['roman']} {row['uppercase']} {row['numbers']} {row['lowercase']}".replace("nan",""), axis=1)
        df["uuid"] = df.text.apply(
            lambda value: uuid5(NAMESPACE_DNS, value))            
        df.rename(axis="columns",
                  mapper={"text": "framework_statement"},
                  inplace=True)
        df = df[["framework_statement",
                 "uuid",
                 "numeric_tag"]]

        return df.to_csv(index=False)

    if 'opm' == provider:
        if not provider_args:
            provider_args = {
                "sheet_name": "Competency Definitions",
                }

        df = pd.read_excel(path, 
                           sheet_name=provider_args['sheet_name'])
        df["framework_statement"] =\
            df["Competency Title"] + " " + df["Competency Definition"] 
        df["uuid"] = df.framework_statement.apply(
            lambda value: uuid5(NAMESPACE_DNS, value))
        df["numeric_tag"]= df.index     
        df = df[["framework_statement",
                 "uuid",
                 "numeric_tag"]]

        return df.to_csv(index=False)

    if 'nist' == provider:
        if not provider_args:
            provider_args = {
                "sheet_name": "Master Task List",
                "sheet_name2": "Master KSA List"
                }
        
        df_task = pd.read_excel(path,
                                sheet_name=provider_args['sheet_name'],
                                skiprows=2
        )
        df_task.columns = ["numeric_tag", "framework_statement", "withdrawn", "blank"]
        df_ksas = pd.read_excel(path,
                                sheet_name=provider_args['sheet_name2'],
                                skiprows=2
        )
        df_ksas.columns = ["numeric_tag", "framework_statement", "withdrawn"]

        df = pd.DataFrame(
                pd.concat(
                    (df_task.iloc[: , :2], df_ksas.iloc[: , :2]),
                    axis=0,
                    ignore_index=True
                ),
                columns=["framework_statement", "numeric_tag"]
        )
        df.dropna(inplace=True)
        df["uuid"] = df.framework_statement.apply(
            lambda value: uuid5(NAMESPACE_DNS, value)
            )
        df = df[["framework_statement",
                 "uuid",
                 "numeric_tag"]]

        return df.to_csv(index=False)

    if 'onet' == provider:
        df = pd.read_csv(path, sep='\n', header=None)
        df.columns = ["framework_statement"]
        df.dropna(inplace=True)
        df["uuid"] = df.framework_statement.apply(
            lambda value: uuid5(NAMESPACE_DNS, value))
        df["numeric_tag"]= df.index     
        df = df[["framework_statement",
                 "uuid",
                 "numeric_tag"]]

        return df.to_csv(index=False)

    if 'esco' == provider:
        df = pd.read_csv(path)
        df.dropna(inplace=True)
        df.rename(axis="columns",
                  mapper={
                      "preferredLabel": "framework_statement",
                      "conceptUri": "numeric_tag"
                  },
                  inplace=True)
        df["uuid"] = df.framework_statement.apply(
            lambda value: uuid5(NAMESPACE_DNS, value))
        df = df[["framework_statement",
                 "uuid",
                 "numeric_tag"]]

        return df.to_csv(index=False)

    if 'simple' == provider:
        with open(path, "r") as obj:
            config = yaml.full_load(obj)
        df = pd.DataFrame(
                {
                    "framework_statement": 
                        config['text_block'].split('\n')
                }
            )
        df['numeric_tag'] = ''
        df["uuid"] = df.framework_statement.apply(
            lambda value: uuid5(NAMESPACE_DNS, value))
        print(df)
        return df.to_csv(index=False)

    if 'ctdl' == provider:
        df = read_jsonld_and_parse(path)
        df.rename(axis="columns",
                mapper={0: "framework_statement",
                        1: "numeric_tag",
                        2: "uuid"},
                inplace=True)
        #  fixes https://www.pivotaltracker.com/n/projects/2354089
        #df.framework_statement =\
        #    df.framework_statement.str.replace('(Core)', '')
        return df.to_csv(index=False)