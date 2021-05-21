from app.db.base_class import Base
from typing import Any, Literal, Optional, Type, TypeVar, Union, Generic, get_args
from pydantic import validator
from fastapi_utils.api_model import APIModel
from enum import Enum
from datetime import datetime
from pydantic.generics import GenericModel


class SortType(Enum):
    ASC = "ASC"
    DESC = "DESC"


class SortData(APIModel):
    column: str
    direction: SortType = SortType.ASC


class FilterType(Enum):
    ENUM = "ENUM"
    DATETIME = "DATETIME"
    VALUE = "VALUE"


EnumFilter = list[str]
DateTimeFilter = tuple[Optional[datetime], Optional[datetime]]
ValueFilter = str
ColumnFiltrationDict = dict[
    str,
    Union[
        tuple[Literal[FilterType.ENUM], EnumFilter],
        tuple[Literal[FilterType.DATETIME], DateTimeFilter],
        tuple[Literal[FilterType.VALUE], ValueFilter],
    ],
]
ColumnFiltrationDictRaw = dict[
    str,
    Union[
        tuple[Literal[FilterType.ENUM], str],
        tuple[Literal[FilterType.DATETIME], str],
        tuple[Literal[FilterType.VALUE], str],
    ],
]

_T = TypeVar("_T", Type[Base], None)


class FilterData(GenericModel, Generic[_T]):
    table: _T = None
    sort: Optional[SortData] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    data: ColumnFiltrationDict = {}

    class Config:
        arbitrary_types_allowed = True

    @validator("sort", pre=True)
    @classmethod
    def validate_sort(cls, value: Union[str, Optional[SortData]]) -> Optional[SortData]:
        """ Validate sort data, also parse from string with ',' delimiter """
        if isinstance(value, str):
            column_name, sort_type, *other = value.split(",")
            assert len(other) == 0
            assert column_name != "", "Column name can not be empty"
            assert sort_type in [e.name for e in SortType], "Invalid sort type"
            return SortData(column=column_name, direction=SortType[sort_type])
        return value

    @validator("sort", pre=False)
    @classmethod
    def validate_sort_column(
        cls, value: Optional[SortData], values: dict[str, Any], **kwargs
    ) -> Optional[SortData]:
        """ Post validate sort value to check a column name """

        TableType: _T = values["table"]

        # On FilterData[Any], skip column verification
        if TableType is not None and value is not None:
            assert value.column in TableType.__table__.columns, (
                f"{value} is not a valid column for table {TableType} "
                f"(Available {', '.join(TableType.__table__.columns)})"
            )

        return value

    @validator("data", pre=True)
    @classmethod
    def validate_data(
        cls, value: Union[ColumnFiltrationDict, ColumnFiltrationDictRaw]
    ) -> ColumnFiltrationDict:
        resulting_dict: ColumnFiltrationDict = {}
        for column_name, comb_value in value.items():
            if isinstance(comb_value[1], str) and comb_value[0] != FilterType.VALUE:
                filtration_value = comb_value[1]
                filtration_type = comb_value[0]

                # Parse enum type from string
                if filtration_type == FilterType.ENUM:
                    resulting_dict[column_name] = (
                        filtration_type,
                        filtration_value.split(","),
                    )

                # Parse datetime type from string
                elif filtration_type == FilterType.DATETIME:
                    start_time: Optional[str]
                    end_time: Optional[str]

                    start_time, end_time, *other = filtration_value.split(",")
                    assert len(other) == 0, "Too much params for datetime"

                    # If it has 0 characters for timestamp, it means None
                    start_time = start_time if start_time != "" else None
                    end_time = end_time if end_time != "" else None

                    # Both can not be None
                    assert (
                        start_time is not None or end_time is not None
                    ), "Both values can not be empty"

                    # Despite being incorrect type, pydantic will format
                    # strings to become a valid datetime
                    resulting_dict[column_name] = (  # type: ignore
                        filtration_type,
                        (start_time, end_time),
                    )
                else:
                    raise NotImplementedError

            # If it is Value type or not string, leave it as it is
            else:
                resulting_dict[column_name] = comb_value  # type: ignore
        return resulting_dict

    @validator("data", pre=False)
    @classmethod
    def validate_data_column(
        cls, value: ColumnFiltrationDict, values: dict[str, Any], **kwargs
    ) -> ColumnFiltrationDict:
        """ Post validate sort value to check a column name """

        TableType: _T = values["table"]

        # On FilterData[None], skip column verification
        if TableType is not None:
            for column_name, (sort_type, sort_value) in value.items():
                assert column_name in TableType.__table__.columns, (
                    f"{column_name} is not a valid column for table {TableType} "
                    f"(Available {', '.join(TableType.__table__.columns)})"
                )

        return value