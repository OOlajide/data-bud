from flipside import Flipside
import os
import pandas as pd

def execute_flipside_query(sql_query: str) -> pd.DataFrame:
    flipside = Flipside(os.environ.get("FLIPSIDE_API_KEY"), "https://api-v2.flipsidecrypto.xyz")
    query_result_set = flipside.query(sql_query)
    return pd.DataFrame(query_result_set.records)