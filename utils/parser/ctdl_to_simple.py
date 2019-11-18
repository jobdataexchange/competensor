import pandas as pd
from pathlib import Path
from json import loads
import jmespath

def read_jsonld_and_parse(file_path):
    obj =\
        loads(
            Path(file_path).read_text()
        )

    records =\
        jmespath.search( 
            "\"@graph\"" 
                "[?\"@type\"==`ceasn:Competency`]." 
                    "[\"ceasn:competencyText\".\"en-us\","
                    "\"ceasn:isPartOf\"," 
                    "\"ceterms:ctid\"]", 
            obj)

    return pd.DataFrame.from_records(records)