pygander
========

.. image:: https://img.shields.io/pypi/v/pygander.svg
    :target: https://pypi.python.org/pypi/pygander
    :alt: Latest PyPI version

.. image:: https://travis-ci.org/kragniz/cookiecutter-pypackage-minimal.png
   :target: https://travis-ci.org/kragniz/cookiecutter-pypackage-minimal
   :alt: Latest Travis CI build status

Kaggle Data Utilities

Usage
-----

Transforms
^^^^^^^^^^
PyGander contains advanced function decorators which allow you to create or replace columns in dataframes using a fun and efficient function-based syntax. 

.. code-block:: python

    import pygander as pg
    import pandas as pd
    
    df = pd.DataFrame(...)
    
    @pg.rowlogic(df)
    def new_column_name(existing_column_name, existing_column_name2:cast_to_type=value_if_na):
        # named elements from rows get passed in 
        # (after being cast to the annotated types or replaced with default values if NA)
        # output is the value for the current row 
        # computed in-place, a new column called 'new_column_name' will be added to df
        ... # complex logic here
        return ... # some value

Take for example, the following dummy code which performs a complex logical operation row-wise on a dataframe with at least three columns, ``a``, ``b`` and ``c``. Assume the columns need to be cast to ints for the operation. This operation could also  create exceptions which need to be handled.

.. code-block:: python

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

Using ``pygander``, we can cut the number of characters required to write this operation in half, and make the syntax _much_ easier to read.

.. code-block:: python

    import pygander as pg

    @pg.rowlogic(df, default_if_exception=pd.NA)
    def with_rowlogic(a: int, b: int, c: int = 7):
        if a < b:
            return 'a < b'
        elif a < 2 * b:
            return 'a < 2b'
        elif a > b:
            raise ValueError('a > b')
        
        return str(c)

The ``ctransf`` decorator also allows for column-wise transformations. Take for example the following pandas script.

.. code-block:: python

    import pandas as pd

    df = pd.DataFrame(...)

    # make a z_score_of_a column in df
    df['z_score_of_a'] = (df['a'] - df['a'].mean()) / (df['a'].std())

The following pygander script is equivalent.

.. code-block:: python

    import pygander as pg
    import pandas as pd


    df = pd.DataFrame(...)

    # make a z_score_of_a column in df using pygander
    @pg.ctransf(df)
    def z_score_of_a(a):
        return (a - a.mean()) / a.std()

Both scripts are equally verbose, but as the number of column references increases, ``ctransf`` becomes a more efficient means of creating column transforms. In addition to reducing at least 5-6 characters per column reference (``df['`` and ``']``), the decorator-and-function syntax is also easier to read.

If your dataframe has column names that aren't "identifiers" and can't be listed as function parameters (leading digits, spaces, symbols, etc.), ``pygander`` offers ``pg.norm_colnames`` a convenient and robust in-place column renaming function.

.. code-block:: python

    >>> df.columns
    Index['  0123 aBC', ' /// e', 'Normal Name']
    >>> pg.norm_colnames(df)
    >>> df.columns
    Index['_0123_abc', '_e', 'normal_name']
    >>> pg.rowlogic(df)
    ... def new_col(_0123_abc, _e, normal_name):
    ...    ... # now you can use the column names as identifiers

Grouper
^^^^^^^

The Grouper class provides a convenient means of selecting certain dataframe splits or column sets. Take the following dataframes:

.. code-block:: python

    k = 100
    df = pd.DataFrame()
    df['rowid'] = list(range(k))
    df['a'] = choices([1, 2, 3], k=k)
    df['b'] = choices(['e','ee','eee'], k=k)
    df['c'] = choices([1, 2, 3, 4, 5, 6], k=k)
    df['target'] = choices([0, 1], k=k)
    
    train=df.head(k//4)
    val = df.head(k//2).tail(k//4)
    test=df.tail(k//2).drop('target', axis=1)

To create a grouper, identify sets of columns and which dataframes you're interested in.

.. code-block:: python

    dfg = pg.Grouper(
         column_groups = {
            'rowid': ['rowid'],
            'x': ['a', 'b', 'c'],
            'y': ['target'],
        },
        train=train,
        test=test,
        val=val
    )

You can then call ``dfg.sel`` to select and combine certain dataframes and column sets. For example, common phases of the kaggle process include data preparation, where you'll want all feature columns for all splits, without row IDs or target data.

.. code-block:: python

    dfg.sel(cg='x')

During training, you'll want feature data and target data for the training set.

.. code-block:: python

    dfg.sel(cg=['x', 'y'], df='train')

During validation, you'll want feature data and target data for the validation set.

.. code-block:: python

    dfg.sel(cg=['x', 'y'], df='val')

And during competition inference, you'll want the row IDs and the feature data for the test set.

.. code-block:: python

    dfg.sel(cg=['rowid', 'x'], df='test')

If you want to see everything, you can call an empty ``dfg.sel``.

.. code-block:: python

    dfg.sel()



Installation
------------

Requirements
^^^^^^^^^^^^

Compatibility
-------------

Licence
-------

Authors
-------

`pygander` was written by `Elias Jaffe <elijaffe173@gmail.com>`_.
