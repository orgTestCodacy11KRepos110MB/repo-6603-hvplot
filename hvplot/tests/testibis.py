"""Ibis works with hvplot"""
import sqlite3
from pathlib import Path

import holoviews as hv
import matplotlib
import pytest

matplotlib.use('agg')

try:
    import duckdb
    import hvplot.ibis  # noqa
    import hvplot.pandas  # noqa
    import ibis
    import pandas as pd
except:
    pytest.skip(allow_module_level=True)

@pytest.fixture
def reference_df():
    return pd.DataFrame(
        {
            "actual": [100, 150, 125, 140, 145, 135, 123],
            "forecast": [90, 160, 125, 150, 141, 141, 120],
            "numerical": [1.1, 1.9, 3.2, 3.8, 4.3, 5.0, 5.5],
            "date": pd.date_range("2022-01-03", "2022-01-09"),
            "string": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        },
    )

def pandas_data(df: pd.DataFrame, *args, **kwargs):
    return df.copy()

def ibis_sqlite_data(df: pd.DataFrame, *args, **kwargs):
    tmpdir = kwargs["tmpdir"]
    filename = str(Path(tmpdir)/"db.db")
    con = sqlite3.Connection(filename)
    df.to_sql("df", con, index=False)
    con = ibis.sqlite.connect(filename)
    return con.table("df")

def ibis_pandas_data(df: pd.DataFrame, *args, **kwargs):
    return ibis.pandas.connect({"df": df}).table("df")

def ibis_duckdb_data(df: pd.DataFrame, *args, **kwargs):
    tmpdir = kwargs["tmpdir"]
    filename = str(Path(tmpdir)/"db.db")
    duckdb_con = duckdb.connect(filename)
    duckdb_con.execute("CREATE TABLE df AS SELECT * FROM df")

    return ibis.duckdb.connect(filename).table("df")

class IbisMemConnection(param.Parameterized):
    def __init__(self, df):
        super().__init__()
        self._table = ibis.memtable(df)
    
    def table(self, df):
        return self._table

def ibis_mem_table(df: pd.DataFrame, *args, **kwargs):
    return IbisMemConnection(df=df)

@pytest.fixture(params=[pandas_data, ibis_pandas_data, ibis_duckdb_data, ibis_sqlite_data, ibis_mem_table])
def data(request, reference_df, tmpdir):
    return request.param(reference_df, tmpdir=tmpdir)

@pytest.fixture(params=["bokeh", "matplotlib", "plotly"])
def backend(request):
    return request.param

@pytest.fixture(params=["date", "numerical", "string"])
def xseries(request):
    return request.param

def test_can_hvplot(xseries, data, backend):
    """hvplot works with Ibis"""
    plot = data.hvplot(x=xseries, y="actual")
    hv.render(plot, backend=backend)

def test_can_hist(data, backend):
    """hist works with Ibis"""
    plot = data.hvplot.hist("actual", bins=3)
    hv.render(plot, backend=backend)