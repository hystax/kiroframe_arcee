import os
import uuid
import pandas as pd
import random
from datetime import datetime, timedelta
import kiroframe_arcee as arcee

LOCAL_PATH = os.path.abspath('example.parquet')
EXAMPLE_ROWS = 100


def gen_row():
    dt = datetime.now() - timedelta(days=random.randint(0, 365))
    ts = int(dt.timestamp())
    return {
        "id": str(uuid.uuid4()),
        "name": [f"user_{ts}"],
        "age": random.randint(18, 65),
        "salary": round(random.uniform(3000, 10000), 2),
        "created_at": dt
    }


def save_dataframe_to_file(df, file_path):
    df.to_parquet(file_path, engine="pyarrow", index=False)


@arcee.track_datasets('df',
                      comment='Remove users with high salary')
# track dataframe changes
def filter_by_salary(threshold, df):
    df.drop(df[df["salary"] > threshold].index, inplace=True)


if __name__ == "__main__":
    with arcee.init("YOU-PROFILING_TOKEN", task_key="test_task"):
        # prepare dataframe
        df = pd.DataFrame([gen_row() for i in range(EXAMPLE_ROWS)])
        save_dataframe_to_file(df, LOCAL_PATH)

        # create Arcee dataset
        dataset = arcee.Dataset(key='test_dataset', description='test dataset')

        # add file
        file_path = f'file://{LOCAL_PATH}'
        dataset.add_file(path=file_path)

        # log new dataset_version (with file)
        arcee.log_dataset(dataset)
        print('Dataset version: ', dataset._version)

        # download
        dataset.download()
        df = dataset.get_dataframe(file_path)

        # process dataset
        filter_by_salary(5000, df)
        save_dataframe_to_file(df, LOCAL_PATH)

        # save changed dataset
        dataset.add_file(path=file_path)
        arcee.log_dataset(dataset)
        print('Dataset version: ', dataset._version)
