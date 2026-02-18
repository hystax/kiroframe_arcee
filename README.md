# Kiroframe_arcee
## *The Kiroframe ML profiling tool by Hystax*

Kiroframe_arcee (short name - Kiro) is a tool that helps you to integrate ML tasks with [Kiroframe](https://my.kiroframe.com/).
This tool can automatically collect executor metadata from the cloud and process stats.

## Installation
Kiroframe_arcee requires Python 3.8+ to run.
To start, install the `kiroframe_arcee` package, use pip:
```sh
pip install kiroframe-arcee
```

## Import
Import the `kiroframe_arcee` module into your code as follows:
```sh
import kiroframe_arcee as kiro
```

## Initialization
To initialize the Kiro collector use the `init` method with the following parameters:
- token (str, required): the profiling token.
- task_key (str, required): the task key for which you want to collect data.
- run_name (str, optional): the run name.
- period (int, optional): Kiro daemon process heartbeat period in seconds (default is 1).

To initialize the collector using a context manager, use the following code snippet:
```sh
with kiro.init(token="YOUR-PROFILING-TOKEN",
               task_key="YOUR-TASK-KEY",
               run_name="YOUR-RUN-NAME",
               period=PERIOD):
    # some code
```

Examples:
```sh
with kiro.init("00000000-0000-0000-0000-000000000000", "linear_regression",
               run_name="My run name", period=1):
    # some code
```

This method automatically handles error catching and terminates Kiro execution.

Alternatively, to get more control over error catching and execution finishing, you can initialize the collector using a corresponding method.
Note that this method will require you to manually handle errors or terminate Kiro execution using the `error` and `finish` methods.
```sh
kiro.init(token="YOUR-PROFILING-TOKEN", task_key="YOUR-TASK-KEY")
# some code
kiro.finish()
# or in case of error
kiro.error()
```

## Sending metrics
To send metrics, use the `send` method with the following parameter:
- data (dict, required): a dictionary of metric names and their respective values (note that metric data values should be numeric).
```sh
kiro.send({"YOUR-METRIC-1-KEY": YOUR_METRIC_1_VALUE, "YOUR-METRIC-2-KEY": YOUR_METRIC_2_VALUE})
```
Example:
```sh
kiro.send({ "accuracy": 71.44, "loss": 0.37 })
```

## Adding hyperparameters
To add hyperparameters, use the `hyperparam` method with the following parameters:
- key (str, required): the hyperparameter name.
- value (str | number, required): the hyperparameter value.
```sh
kiro.hyperparam(key="YOUR-PARAM-KEY", value=YOUR_PARAM_VALUE)
```
Example:
```sh
kiro.hyperparam("EPOCHS", 100)
```

## Tagging task run
To tag a run, use the `tag` method with the following parameters:
- key (str, required): the tag name.
- value (str | number, required): the tag value.
```sh
kiro.tag(key="YOUR-TAG-KEY", value=YOUR_TAG_VALUE)
```
Example:
```sh
kiro.tag("Algorithm", "Linear Learn Algorithm")
```

## Adding milestone
To add a milestone, use the `milestone` method with the following parameter:
- name (str, required): the milestone name.
```sh
kiro.milestone(name="YOUR-MILESTONE-NAME")
```
Example:
```sh
kiro.milestone("Download training data")
```

## Adding stage
To add a stage, use the `stage` method with the following parameter:
- name (str, required): the stage name.
```sh
kiro.stage(name="YOUR-STAGE-NAME")
```
Example:
```sh
kiro.stage("preparing")
```

## Datasets
### Logging
Logging a dataset allows you to create a dataset or a new version of 
the dataset if the dataset has already been created, but has been changed.
To create a dataset, use the `Dataset` class with the following parameters:

Dataset parameters:
- key (str, required): the unique dataset key.
- name (str, optional): the dataset name.
- description (str, optional): the dataset description.
- labels (list, optional): the dataset labels.

Version parameters:
- aliases (list, optional): the list of aliases for this version.
- meta (dict, optional): the dataset version meta.
- timespan_from (int, optional): the dataset version timespan from.
- timespan_to (int, optional): the dataset version timespan to.
```sh
dataset = kiro.Dataset(key='YOUR-DATASET-KEY', 
                       name='YOUR-DATASET-NAME',
                       description="YOUR-DATASET-DESCRIPTION",
                       ...
                       )
dataset.labels = ["YOUR-DATASET-LABEL-1", "YOUR-DATASET-LABEL-2"]
dataset.aliases = ['YOUR-VERSION-ALIAS']
```
To log a dataset, use the `log_dataset` method with the following parameters:
- dataset (Dataset, required): the dataset object.
- comment (str, optional): the usage comment.
```sh
kiro.log_dataset(dataset=dataset, comment='LOGGING_COMMENT')
```

### Using
To use a dataset, use the `use_dataset` method with dataset `key:version`. 
Parameters:
- dataset (str, required): the dataset identifier in key:version format.
- comment (str, optional): the usage comment.
```sh
dataset = kiro.use_dataset(
    dataset='YOUR-DATASET-KEY:YOUR-DATASET-VERSION-OR-ALIAS')
```

### Adding files and downloading
You can add or remove files from dataset and download it as well. 
Supported file paths:
- `file://` - the local files.
- `s3://` - the amazon S3 files.

adding / removing files

local:
```sh
dataset.remove_file(path='file://LOCAL_PATH_TO_FILE_1')
dataset.add_file(path='file://LOCAL_PATH_TO_FILE_2')
kiro.log_dataset(dataset=dataset)
```
s3:
```sh
os.environ['AWS_ACCESS_KEY_ID'] = 'AWS_ACCESS_KEY_ID'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'AWS_SECRET_ACCESS_KEY'
dataset.remove_file(path='s3://BUCKET/PATH_1')
dataset.add_file(path='s3://BUCKET/PATH_2')
kiro.log_dataset(dataset=dataset)
```
downloading:
Parameters:
- overwrite (bool, optional): overwrite an existing dataset or skip 
downloading if it already exists.
```sh
dataset.download(overwrite=True)
```
Example:
```sh
# use version v0, v1 etc, or any version alias: my_dataset:latest
dataset = kiro.use_dataset(dataset='my_dataset:V0')
path_map = dataset.download()
for local_path in path_map.values():
    with open(local_path, 'r'):
        # read downloaded file

new_dataset = kiro.Dataset('new_dataset')
new_dataset.add_file(path='s3://ml-bucket/datasets/training_dataset.csv')
kiro.log_dataset(dataset=new_dataset)
new_dataset.download()
```

## Creating models
To create a model, use the `model` method with the following parameters:
- key (str, required): the unique model key.
- path (str, optional): the run model path.
```sh
kiro.model(key="YOUR-MODEL-KEY", path="YOUR-MODEL-PATH")
```
Example:
```sh
kiro.model("my_model", "/home/user/my_model")
```

## Setting model version
To set a custom model version, use the `model_version` method with the following parameter:
- version (str, required): the version name.
```sh
kiro.model_version(version="YOUR-MODEL-VERSION")
```
Example:
```sh
kiro.model_version("1.2.3-release")
```

## Setting model version alias
To set a model version alias, use the `model_version_alias` method with the following parameter:
- alias (str, required): the alias name.
```sh
kiro.model_version_alias(alias="YOUR-MODEL-VERSION-ALIAS")
```
Example:
```sh
kiro.model_version_alias("winner")
```

## Setting model version tag
To add tags to a model version, use the `model_version_tag` method with the following parameters:
- key (str, required): the tag name.
- value (str | number, required): the tag value.
```sh
kiro.model_version_tag(key="YOUR-MODEL-VERSION-TAG-KEY", value=YOUR_MODEL_VERSION_TAG_VALUE)
```
Example:
```sh
kiro.model_version_tag("env", "staging demo")
```

## Creating artifacts
To create an artifact, use the `artifact` method with the following parameters:
- path (str, required): the run artifact path.
- name (str, optional): the artifact name.
- description (str, optional): the artifact description.
- tags (dict, optional): the artifact tags.
```sh
kiro.artifact(path="YOUR-ARTIFACT-PATH",
              name="YOUR-ARTIFACT-NAME",
              description="YOUR-ARTIFACT-DESCRIPTION",
              tags={"YOUR-ARTIFACT-TAG-KEY": YOUR_ARTIFACT_TAG_VALUE})
```
Example:
```sh
kiro.artifact("https://s3/ml-bucket/artifacts/AccuracyChart.png",
              name="Accuracy line chart",
              description="The dependence of accuracy on the time",
              tags={"env": "staging"})
```

## Setting artifact tag
To add a tag to an artifact, use the `artifact_tag` method with the following parameters:
- path (str, required): the run artifact path.
- key (str, required): the tag name.
- value (str | number, required): the tag value.
```sh
kiro.artifact_tag(path="YOUR-ARTIFACT-PATH",
                  key="YOUR-ARTIFACT-TAG-KEY",
                  value=YOUR_ARTIFACT_TAG_VALUE)
```
Example:
```sh
kiro.artifact_tag("https://s3/ml-bucket/artifacts/AccuracyChart.png",
                  "env", "staging demo")
```

## Finishing task run
To finish a run, use the `finish` method.
```sh
kiro.finish()
```

## Failing task run
To fail a run, use the `error` method.
```sh
kiro.error()
```
