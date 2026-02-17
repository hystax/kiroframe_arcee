import kiroframe_arcee as kiro

with kiro.init("test", "simple"):
    dataset = kiro.Dataset(key='test_dataset', description='test dataset')

    # adding file
    dataset.add_file(path=__file__)

    # log new dataset_version (with file)
    kiro.log_dataset(dataset)
    print('Actual dataset version: ', dataset._version)

    # downloading
    dataset.download()

    # remove file from dataset
    dataset.remove_file(path=__file__)

    # log new dataset_version (without files)
    kiro.log_dataset(dataset)
    print('Actual dataset version: ', dataset._version)
