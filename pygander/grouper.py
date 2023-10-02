from typing import Dict, List, Union, Any, Callable

import pandas as pd


def _aggvals(data: Dict[str, Any], query: Union[str, List[str], None], agg: Callable):
    """Aggregate values selected via the query.

    Args:
        data (Dict[str, Any]): Original dictionary of key/value pairs
        query (Union[str, List[str], None]): A key or list of keys, or none for all
        agg (Callable): _description_

    Raises:
        KeyError: Query key is not found in the data.
        ValueError: Inappropriate query datatype

    Returns:
        agg of queried values
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
        """Select a group of columns or dataframes

        Args:
            cg (Union[str, List[str], None], optional): List of column groups, a single column group, or None for all columns. Defaults to None.
            df (Union[str, List[str], None], optional): List of dataframes, a dataframe key, or None for all. Defaults to None.

        Returns:
            pd.DataFrame: Selected dataframes.
        """
        sel_cols = _aggvals(self.column_groups, cg, _agg_str_list)
        sel_dfs = _aggvals(self.dataframes, df, pd.concat)
        return sel_dfs[sel_cols]
