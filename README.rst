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

Grouper
^^^^^^^

.. code-block:: python

    :caption: Constructing demo datasets
      k = 100
    df = pd.DataFrame()
    df['rowid'] = list(range(k))
    df['a'] = choices([1, 2, 3], k=k)
    df['b'] = choices(['e','ee','eee'], k=k)
    df['c'] = choices([1, 2, 3, 4, 5, 6], k=k)
    df['target'] = choices([0, 1], k=k)
    
    column_groups = {
        'rowid': ['rowid'],
        'x': ['a', 'b', 'c'],
        'y': ['target'],
    }
    
    train=df.head(k//4)
    val = df.head(k//2).tail(k//4)
    test=df.tail(k//2).drop('target', axis=1)

.. code-block:: python

    :caption: Instantiating Grouper class
    dfg = Grouper(
        column_groups,
        train=train,
        test=test,
        val=val
    )

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

    @pg.rowlogic(df, default_if_exception=pd.NA)
    def with_rowlogic(a: int, b: int, c: int = 7):
        if a < b:
            return 'a < b'
        elif a < 2 * b:
            return 'a < 2b'
        elif a > b:
            raise ValueError('a > b')
        
        return str(c)

    

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
