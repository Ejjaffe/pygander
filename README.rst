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
