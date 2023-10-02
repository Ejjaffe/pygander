from pygander.grouper import Grouper
import pandas as pd
from random import choices

def test_sel():
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
    
    dfg = Grouper(
        column_groups,
        train=train,
        test=test,
        val=val
    )
    
    assert set(dfg.sel().columns) == set(train.columns), '.sel() returns all columns'
    assert set(dfg.sel().index) == set(df.index), '.sel() returns all indexes'
    assert set(dfg.sel('x').columns) == set(column_groups['x']), '.sel("one group") columns'
    assert set(dfg.sel(['x']).columns) == set(column_groups['x']), '.sel(["one group"]) columns'
    assert set(dfg.sel(['x','y']).columns) == set(column_groups['x'] + column_groups['y']), '.sel(["two","groups"]) columns'
    assert set(dfg.sel(df='train').index) == set(train.index), '.sel(dataframes="one_df") returns all one_df indexes'
    assert set(dfg.sel(cg=['x','y'], df=['train','test']).index) == set(df.index) - set(val.index), 'column groups + df groups, testing df groups'
    assert set(dfg.sel(cg=['x','y'], df=['train','test']).columns) == set(column_groups['x'] + column_groups['y']), 'column groups + df groups, testing col groups'
