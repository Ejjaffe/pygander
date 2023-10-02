from typing import Dict, List, Union, Any, Callable

import pandas as pd


def _aggvals(data: Dict[str, Any], query: Union[str, List[str], None], agg: Callable):
    """
    Aggregate values from a dictionary based on a query.

    :param data: A dictionary containing string-key: value pairs.
    :param query: Query parameter specifying which values to return (str, list of str, or None).
    :param agg: Aggregation function to join values together.
    :return: Aggregated value(s) based on the query.
    """
    if query is None:
        return agg(data.values())
    elif isinstance(query, str):
        if query in data:
            return data[query]
        else:
            raise KeyError(f"Key '{query}' not found in the dictionary.")
    elif isinstance(query, list):
        if all(qkey in data for qkey in query):
            values = [data[key] for key in query]
            return agg(values)
        else:
            raise KeyError(
                f"One or more keys in the query were not found in the dictionary: {list(qkey for qkey in query if qkey not in data)}"
            )
    else:
        raise ValueError(
            "Invalid query parameter. Must be a string, list of strings, or None.")


def _agg_str_list(a: Union[List[List[str]], List[str]]):
    unique_str = set()
    for strlist in a:
        if isinstance(strlist, list):
            unique_str.update(strlist)
        else:
            unique_str.add(strlist)
    return sorted(unique_str)


class Grouper:
    def __init__(self, column_groups: Dict[str, List[str]], **dataframes: pd.DataFrame):
        """Grouper for a DataFrame

        Args:
            column_type_mapping (Dict[str, List[str]]): A dict of {'grouping_key':['DataFrameColumn1',...]}
            **kwargs (pd.DataFrame): named pandas dataframes 
        """
        self.column_groups = column_groups
        self.dataframes = dataframes

    def sel(self, cg: Union[str, List[str], None] = None, df: Union[str, List[str], None] = None) -> pd.DataFrame:
        """
        Select columns of a specific type from the data.

            :param column_type: The type of columns to select, string.
            :param data_split: The data split to operate on ("train", "test", or "all").
            :return: A DataFrame containing the selected columns.
        """
        sel_cols = _aggvals(self.column_groups, cg, _agg_str_list)
        sel_dfs = _aggvals(self.dataframes, df, pd.concat)
        return sel_dfs[sel_cols]
