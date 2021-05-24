from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from .base import BaseCommand
from app.core.config import settings
from app import schemas
import pandas as pd
import io

if TYPE_CHECKING:
    from app.core.console.connection_manager import ConnectionManagers


class DiskFormat(BaseCommand[pd.DataFrame]):
    _command = "df"

    def _process_stdout(self, log: schemas.ConsoleLog) -> pd.DataFrame:
        super()._process_stdout(log)
        df = pd.read_table(io.StringIO(log.stdout), delim_whitespace=True)
        df = df.loc[df.on.isnull()]
        return df