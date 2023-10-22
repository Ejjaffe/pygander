"""Convenient row/column-wise transformation utilities."""

import pandas as pd
import inspect
import re
from collections import defaultdict
from typing import Callable, Union, Literal, Any


def _apply_param_logic(
    param_name: str,
    param_obj: inspect.Parameter,
    value: Any,
    func_name: str,
    strict_typecast: Union[bool, Literal["default"]],
):
    """Signature.bind doesn't enforce annotations or recognize pd.NA or np.nan as None, so we need to roll our own."""

    # apply defaults if None or NA
    if pd.isna(value):
        return param_obj.default

    # not NA and no type annotation? no problem!
    if param_obj.annotation == inspect._empty:
        return value

    # attempt to cast to the annotated type
    # TODO: maybe allow custom casting functions via rowmap? could be cast in-function though
    try:
        return param_obj.annotation(value)

    except Exception as e:
        if strict_typecast == "default":
            # we tried casting but it failed, return the default

            # if we also got a strict_typecast='default' but we have no default
            if param_obj.default == inspect._empty:
                raise ValueError(
                    f'You set `strict_typecast="default"` but {param_name} has no default'
                    " value, and it needs one because the value "
                    f"`{value}` raised an exception during"
                    f" casting to `{param_obj.annotation.__name__}, which was:"
                    f" {e}. Please provide a default value for {param_name} in the"
                    f" {func_name} signature."
                )

            return param_obj.default

        elif strict_typecast:
            # failed to typecast, time to vomit
            raise TypeError(
                f"You specified that parameter `{param_name}` should be of type"
                f"`{param_obj.annotation.__name__} but the value "
                f"`{value}` raised an exception during"
                f" casting, which was: {e}. To use the specified default value"
                f" for your parameter, set `strict_typecast='default'`"
            )

    # issue with typecast and strict_typecast = False, just return the value as-is
    return value


def _apply_func_to_row(
    func: Callable,
    row: pd.Series,
    strict_typecast: Union[bool, Literal["default"]],
    default_if_exception: Any = None,
):
    sig = inspect.signature(func)

    # reduce to requested columns and apply param logic
    # we ensured the parameter names were column names in rowlogic
    row_params = {
        param_name: _apply_param_logic(
            param_name=param_name,
            param_obj=sig.parameters[param_name],
            value=param_value,
            func_name=func.__name__,
            strict_typecast=strict_typecast,
        )
        for param_name, param_value in row.to_dict().items()
        if param_name in sig.parameters
    }

    try:
        return func(**row_params)
    except Exception as e:  # (ValueError, TypeError) as e:
        if default_if_exception is None:
            raise e
        else:
            return default_if_exception


def rowlogic(
    df: pd.DataFrame,
    default_if_exception: Any = None,
    overwrite_col: bool = True,
    strict_typecast: Union[bool, Literal["default"]] = "default",
):
    """Function decorator for row-wise column transformations.

    The name of the function is the resulting column name in the dataframe. The parameter names are 
    the values in each row of the columns with the same names. Values can be cast to a given type by 
    specifying a type via annotation. Default values for parameters can be provided in the case of 
    a `None`, `pd.NA`, or `np.nan`.

    ```python
    @pg.rowlogic(df) #, default_if_exception=pd.NA, overwrite_col=True, strict_typecast='default')
    def result_column_name(existing_column_name, existing_column_name2:cast_to_type=value_if_na):
        # named elements from rows get passed in
        # output is the value for that row in the 'result_column_name' column.
        # computed in-place 
        ... # complex logic here
        return ... # some value 
    ```

    Parameters:
    -----------
        df (pd.DataFrame): Dataframe to use for the row-wise column transformation.

        default_if_exception (Any, optional): A default value to use when the wrapped function raises an exception. If left 
            as `None`, exceptions will still be raised. Popular values are `pd.NA` or `np.nan`. Defaults to `None`.

        overwrite_col (bool, optional): If `True`, allows overwriting an existing column with the same name as the wrapped function. Defaults to True.

        strict_typecast (Union[bool, Literal['default']], optional): If `True`, an error is raised if a value 
            cannot be cast to the type specified via annotation. If `False` and the value cannot be cast to the type 
            specified via annotation, the value is returned as-is. Defaults to "default", which returns the default value 
            specified for the parameter if the value cannot be cast to the type specified via annotation.

    Raises:
    -------
        ValueError: The function name is an existing column in your dataframe and `overwrite_col=False`.

        KeyError: One or more parameter names are not column names in the dataframe.

        Exception: Any exceptions from the wrapped function when `default_if_exception=None`.

        ValueError: `strict_typecast=True` and the casting to the annotated type failed.

        ValueError: `strict_typecast="default"` and the casting to the annotated type failed but a default value for that column was not provided in the signature.

    Usage:
    ------
    The following code snippets are equivalent:
    ```python
    def without_rowlogic(row:pd.Series):
        try:
            if int(row['a']) < int(row['b']):
                return 'a < b'
            elif int(row['a']) < 2 * int(row['b']):
                return 'a < 2b'
            elif int(row['a']) > int(row['b']):
                raise ValueError('a > b')
        except Exception as e:
            return pd.NA
        
        return str(int(row['c'] if row.notna()['c'] else 7))

    df['without_rowlogic'] = [without_rowlogic(row) for idx, row in df.iterrows()]
    ```
    And:
    ```python
    @pg.rowlogic(df, default_if_exception=pd.NA)
    def with_rowlogic(a: int, b: int, c: int = 7):
        if a < b:
            return 'a < b'
        elif a < 2 * b:
            return 'a < 2b'
        elif a > b:
            raise ValueError('a > b')
        
        return str(c)
    ```
    """
    def decorator(func):
        parameters = inspect.signature(func).parameters

        missing_cols = list(set(parameters) - set(df.columns))
        if missing_cols:
            raise KeyError(
                f"The parameter(s) {missing_cols} in your function `{func.__name__}` are not column names "
                f"in your dataframe. The columns are {list(df.columns)}."
            )

        if not overwrite_col and func.__name__ in df.columns:
            raise ValueError(
                f"The function name {func.__name__} is an existing column name in "
                "your dataframe and `overwrite_col` is set to `False`. If you "
                "meant to overwrite the column, set `overwrite_col=True` in the "
                "decorator."
            )

        df[func.__name__] = [
            _apply_func_to_row(
                func=func,
                row=row,
                default_if_exception=default_if_exception,
                strict_typecast=strict_typecast,
            )
            for idx, row in df.iterrows()
        ]

    return decorator

def ctransf(df: pd.DataFrame, overwrite_col: bool = True,):
    """
    Function decorator for inplace column transformations.

    ```python
    @pg.ctransf(df)
    def result_column_name(existing_column_name, existing_column_name2):
        # columns from df get passed in as pd.Series objects
        # output is a new column (iterable/pd.Series) that gets added to df as result_column_name
        return existing_column_name / existing_column_name2.sum() 
    ```
    
    Parameters:
    -----------
        df (pd.DataFrame): The dataframe to transform columns in.

        overwrite_col (bool): If False, raises a ValueError when the name of the function is an existing column. Defaults to True.

    Raises:
    -------
        KeyError: One or more parameters is not a column name in the df.

        ValueError: `overwrite_col=False` and the function name is an existing column name in the df.

    Usage:
    ------
    Use `ctsf` to create column transformations in-place without typing `df['...']` over and over. For example:

    ```python
    import pygander as pg
    import pandas as pd


    df = pd.DataFrame(...)

    # make a z_score_of_a column in df using pygander
    @pg.ctransf(df)
    def z_score_of_a(a):
        return (a - a.mean()) / a.std()
    ```
    is equivalent to:
    ```python
    import pandas as pd


    df = pd.DataFrame(...)

    # make a z_score_of_a column in df
    df['z_score_of_a'] = (df['a'] - df['a'].mean()) / (df['a'].std())
    ```
    In addition to reducing at least 5 characters per column reference (`d['` and `']`), the `ctransf` syntax is also easier to read.
    """
    def decorator(func):
        parameters = inspect.signature(func).parameters

        missing_cols = list(set(parameters) - set(df.columns))
        if missing_cols:
            raise KeyError(
                f"The parameter(s) {missing_cols} in your function `{func.__name__}` are not column names "
                f"in your dataframe. The columns are {list(df.columns)}."
            )

        if not overwrite_col and func.__name__ in df.columns:
            raise ValueError(
                f"The function name {func.__name__} is an existing column name in "
                "your dataframe and `overwrite_col` is set to `False`. If you "
                "meant to overwrite the column, set `overwrite_col=True` in the "
                "decorator."
            )

        df[func.__name__] = func(**{cname:df[cname] for cname in parameters})

    return decorator

def _normalize_column_name(s:str):
    # replace necessary whitespace with _
    s = re.sub(r'[\s]', '_', s.strip())
    # remove any remaining non-identifier chars
    s = re.sub(r'[^0-9a-zA-Z_]', '', s)
    # make leading digits start with an underscore
    s = re.sub(r'^(\d)', r'_\1', s)
    return s.strip().lower()

def norm_colnames(df:pd.DataFrame):
    """
    Normalize column names of a Pandas DataFrame in-place.

    This function makes column names suitable as variable names and ensures
    that duplicates have suffixes to make them unique. 
    
    The string conversion first replaces all 
    whitespace with underscores. Then it removes non-alphanumeric and 
    non-underscore characters and ensures the name starts with a non-digit 
    character by prepending an underscore if needed.

    `'  0123 aBc '` -> `'_0123_abc'`

    Parameters:
    -----------
        df (pd.DataFrame): The Pandas DataFrame with columns to be normalized.
    """
    normalized_columns = df.columns.map(_normalize_column_name)
    seen = defaultdict(int)
    
    new_columns = []
    for col in normalized_columns:
        if seen[col] == 0:
            new_columns.append(col)
        else:
            new_columns.append(f"{col}_{seen[col]}")
        seen[col] += 1

    df.columns = new_columns
