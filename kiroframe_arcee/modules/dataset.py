import os
import asyncio
import threading
from typing import List, Dict
from kiroframe_arcee.modules.providers import local_file, amazon
from kiroframe_arcee.modules.dataframe import init_arcee_dataframe

LOCAL_PREFIX = 'file://'
S3_PREFIX = 's3://'
BASE_PATH = 'kiroframe/datasets/%s/'


class DatasetThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exception = None

    def run(self):
        try:
            if self._target:
                self._target(*self._args, **self._kwargs)
        except Exception as e:
            self.exception = e


class Dataset(object):
    __slots__ = ('key', 'name', 'description', 'labels', 'meta',
                 'timespan_from', 'timespan_to', 'aliases',
                 '_tasks', '_files', '_version')

    def __init__(self, key: str, name: str = None, description: str = None,
                 labels: List[str] = None, meta: Dict = None,
                 timespan_from: int = None, timespan_to: int = None,
                 aliases: List[str] = None):
        self._tasks: List = []
        self._files: Dict = {}
        self._version: int = None
        self.key: str = key
        self.name: str = name
        self.description: str = description
        self.labels: List[str] = labels or []
        self.meta: Dict = meta or {}
        self.timespan_from: int = timespan_from
        self.timespan_to: int = timespan_to
        self.aliases: List[str] = aliases or []

    @classmethod
    def from_response(cls, response):
        version = response.pop('version', {})
        files = version.pop('files', [])
        response.update(version)
        obj = cls(**{
            k: response.get(k) for k in cls.__slots__ if k in response
        })
        obj._version = version['version']
        if files:
            obj.replace_files(files)
        return obj

    def replace_files(self, files):
        self._files = {f['path']: {
            '_id': f['_id'],
            'path': f['path'],
            'size': f['size'],
            'digest': f['digest'],
        } for f in files}

    @property
    def __dict__(self):
        res = dict()
        for k in self.__slots__:
            if k.startswith('_'):
                continue
            value = getattr(self, k)
            if value:
                res[k] = getattr(self, k)
        files = []
        for f in self._files.values():
            files.append({
                'path': f['path'],
                'size': f['size'],
                'digest': f['digest'],
            })
        res['files'] = files
        return res

    def _get_provider(self, path):
        if path.startswith(LOCAL_PREFIX):
            return local_file, path.strip(LOCAL_PREFIX)
        elif path.startswith(S3_PREFIX):
            return amazon, path
        else:
            raise TypeError('Unhandled path type')

    def _add_file(self, path):
        provider, local_path = self._get_provider(path)
        digest, size = asyncio.run(provider.get_file_info(local_path))
        self._files[path] = {
            'path': path,
            'size': size,
            'digest': digest
        }

    def add_file(self, path):
        if path in self._files and self._version is None:
            return
        self._version = None
        self._files[path] = None
        thr = DatasetThread(target=self._add_file, args=(path, ))
        thr.start()
        self._tasks.append(thr)

    def remove_file(self, path):
        if path in self._files:
            del self._files[path]

    def wait_ready(self):
        for task in self._tasks:
            task.join()
            if task.exception:
                raise task.exception

    def get_dataset_name(self):
        return f'{self.key}:V{self._version}'

    def _get_file_destination(self, dataset_name=None):
        if dataset_name is None:
            dataset_name = self.get_dataset_name()
        return BASE_PATH % dataset_name

    def _get_file_name(self, path):
        return path.split('/')[-1]

    def _get_download_path(self, path, destination=None):
        if not destination:
            dataset_name = self.get_dataset_name()
            destination = self._get_file_destination(dataset_name)
        return destination + self._get_file_name(path)

    def download(self, overwrite=True) -> dict:
        download_map = dict()
        if self._version is None:
            raise TypeError('Dataset is not logged')
        name = self.get_dataset_name()
        print('Downloading %s' % name)
        for path, file in self._files.items():
            destination = self._get_file_destination(dataset_name=name)
            file_name = self._get_file_name(path)
            download_path = self._get_download_path(path, destination)
            download_map[path] = download_path
            if not overwrite and os.path.isfile(download_path):
                continue
            thr = DatasetThread(
                target=self._download, args=(file, destination, file_name))
            thr.start()
            self._tasks.append(thr)
        self.wait_ready()
        print('Download completed: %s' % name)
        return download_map

    def _download(self, file, destination, file_name):
        digest = file['digest']
        path = file['path']
        provider, local_path = self._get_provider(path)
        asyncio.run(
            provider.download(
                local_path, digest, destination, file_name
            )
        )

    def get_dataframe(self, path):
        if path not in self._files:
            raise TypeError('The file %s is not part of the dataset' % path)
        file = self._files.get(path) or {}
        file_id = file.get('_id')
        if not file or not file_id:
            raise TypeError('The file %s is not logged' % path)
        local_path = self._get_download_path(path)
        if not os.path.exists(local_path):
            raise ValueError('File %s is not downloaded' % local_path)
        return init_arcee_dataframe(file_id, local_path)
