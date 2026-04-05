import concurrent.futures
import os
import sys
import subprocess

from typing import Optional

from kiroframe_arcee.utils import run_async

EXECUTABLE_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
MAX_DIFF_SIZE = 3 * 1024 * 1024  # 3MB


class Collector:
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

    @staticmethod
    def __get_remote() -> str:
        return subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=EXECUTABLE_DIR
        ).decode('UTF-8').strip()

    @staticmethod
    def __get_branch() -> str:
        return subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=EXECUTABLE_DIR).decode('UTF-8').strip()

    @staticmethod
    def __get_commit_id() -> str:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=EXECUTABLE_DIR).decode('UTF-8').strip()

    @staticmethod
    def __get_status() -> str:
        try:
            subprocess.check_call(["git", "diff", "--exit-code", "--quiet"],
                                  cwd=EXECUTABLE_DIR)
            return "clean"
        except subprocess.CalledProcessError:
            return "dirty"

    @staticmethod
    def __get_diff() -> str:
        return subprocess.check_output(
            ["git", "diff", "HEAD"],
            cwd=EXECUTABLE_DIR).decode('UTF-8').strip()

    @classmethod
    def _collect(cls) -> Optional[dict]:
        try:
            result = {
                "remote": cls.__get_remote(),
                "branch": cls.__get_branch(),
                "commit_id": cls.__get_commit_id(),
                "status": cls.__get_status()
            }
            diff_truncated = False
            diff = cls.__get_diff()
            if len(diff) > MAX_DIFF_SIZE:
                diff = diff[:MAX_DIFF_SIZE]
                diff_truncated = True
            result.update({
                "diff": diff,
                "diff_truncated": diff_truncated
            })
            return result
        except (FileNotFoundError, subprocess.CalledProcessError):
            return

    @classmethod
    async def collect(cls):
        return await run_async(cls._collect, executor=cls.executor)
