from app import schemas
from typing import Any, Optional, TypeVar, TypedDict
from .base import BaseCommand

_T = TypeVar("_T")


class BaseDirCommand(BaseCommand[_T]):
    def __call__(
        self, *, cd: Optional[str] = None, dirname: str = "", **kwargs: str
    ) -> _T:
        return super().__call__(cd=cd, dirname=dirname, **kwargs)

    @classmethod
    def _create_command(
        cls, *, cd: Optional[str] = None, dirname: str = "", **kwargs: str
    ) -> list[str]:
        command = super()._create_command(cd=cd, **kwargs)
        return command[:-1] + [command[-1] + (" " + dirname if dirname != "" else "")]


class ListDirectoryCommand(BaseDirCommand[set[str]]):
    _command = "ls"

    def _process_stdout(self, log: schemas.ConsoleLog) -> set[str]:
        super()._process_stdout(log)
        if "No such file or directory" in log.stdout:
            raise NotADirectoryError(log.stdout)
        return set(log.stdout.split())


class CreateDirectoryCommand(BaseDirCommand[bool]):
    _command = "mkdir"

    def _process_stdout(self, log: schemas.ConsoleLog) -> bool:
        if "File exists" in log.stdout:
            return False
        super()._process_stdout(log)
        return True


class RemoveDirectoryCommand(BaseDirCommand[None]):
    _command = "rm -rf"


class FilesystemData(TypedDict):
    filesystem: str
    total: int
    used: int
    available: int
    use_percentage: str
    mounted_on: str


class DiskFormat(BaseDirCommand[list[FilesystemData]]):
    _command = "df"

    def _process_stdout(self, log: schemas.ConsoleLog) -> list[FilesystemData]:
        super()._process_stdout(log)
        assert "Filesystem" in log.stdout, "Invalid output got from df command"
        result: list[FilesystemData] = []
        for line in log.stdout.splitlines()[1:]:
            words = line.split()
            words = list(filter(lambda s: s != "", words))
            if len(words) != 6:
                continue
            fs, total, used, available, use_percentage, mounted_on = words
            result.append(
                {
                    "filesystem": fs,
                    "total": int(total) * 1024,
                    "used": int(used) * 1024,
                    "available": int(available) * 1024,
                    "use_percentage": use_percentage,
                    "mounted_on": mounted_on,
                }
            )
        return result