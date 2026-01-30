from typing import Dict, Any
from pathlib import Path
import pandas as pd


class ArceeDataframe(pd.DataFrame):
    def __init__(self, *args, file_id, **kwargs):
        super().__init__(*args, **kwargs)
        self._file_id = file_id

    @property
    def file_id(self):
        return self._file_id


def collect_stats(df: pd.DataFrame) -> Dict[str, Any]:
    return {
        'shape': tuple(df.shape),
        'dtype': {c: str(df[c].dtype) for c in df.columns},
        'index': {
            'type': type(df.index).__name__,
            'dtype': str(df.index.dtype),
            'len': len(df.index),
        },
        'size': df.memory_usage(deep=False).to_dict()
    }


def init_arcee_dataframe(file_id, local_path):
    path = Path(local_path)
    if path.suffix == '.csv':
        df = pd.read_csv(path)
    elif path.suffix in {'.xls', '.xlsx'}:
        df = pd.read_excel(path)
    elif path.suffix == '.parquet':
        df = pd.read_parquet(path)
    else:
        raise ValueError('Unsupported file type: %s' % path.suffix)
    return ArceeDataframe(df, file_id=file_id)
