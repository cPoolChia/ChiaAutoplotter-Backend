from typing import Any, Callable, Optional, Union, Literal, cast

import celery
import pandas as pd
from app import schemas, crud
from app.api import deps
from app.celery import celery as celery_app
from fastapi import Depends
from sqlalchemy.orm import Session
from pydantic import ValidationError


# @celery_app.task(bind=True)
# def process_customers_table(
#     self: celery.Task,
#     filename: str,
#     company_id: int,
#     column_mapping: dict[str, str],
#     sheetname: Optional[str] = None,
#     *,
#     storage_factory: Callable[[], BaseObjectStorage] = create_storage,
#     db_factory: Callable[[], Session] = lambda: next(deps.get_db()),
# ) -> Any:
#     db = db_factory()
#     storage = storage_factory()

#     # All the columns with other_info should be gathered in a list and renamed
#     other_info_columns = [k for k, v in column_mapping.items() if v == "other_info"]
#     for i, k in enumerate(other_info_columns):
#         column_mapping[k] = f"other_info{i}"

#     # All columns with contract should be renamed and loaded separately
#     contract_columns = [k for k, v in column_mapping.items() if v == "contract"]
#     for i, k in enumerate(contract_columns):
#         column_mapping[k] = f"contract{i}"

#     file_type = filename.split(".")[-1]
#     file = storage.download_file(filename)
#     df = read_table(
#         file, "csv" if file_type == "csv" else "excel", column_mapping, sheetname
#     )

#     # Keeps track of skipped rows and columns
#     # If the row is skipped completely, it will be in skipped
#     # If only some fields, it will be in formatted

#     formatted: dict[int, list[str]] = {}

#     for i, row in df.iterrows():
#         customer_dict: dict[str, Union[str, list[str], None]] = row.to_dict()
#         # Collect all other_info fields in a list
#         customer_dict["other_info"] = [
#             v
#             for i, _ in enumerate(other_info_columns)
#             if (n := f"other_info{i}") in customer_dict
#             and (v := customer_dict[n]) is not None
#         ]

#         # Validate all fields, convert it fo schemas.CustomerBase
#         skipped_fields: list[str] = []
#         try:
#             customer_data = schemas.CustomerFromExcel(**customer_dict)
#         except ValidationError as e:
#             # If some fields do not pass, ignore them
#             for error in e.errors():
#                 field = error["loc"][0]
#                 del customer_dict[field]
#                 skipped_fields.append(field)
#             customer_data = schemas.CustomerFromExcel(**customer_dict)

#         db_obj = crud.customer.create(
#             db,
#             obj_in=schemas.CustomerCreateExtended(
#                 company_id=company_id, **customer_data.dict()
#             ),
#             commit=skipped_fields != [],
#         )
#         if skipped_fields != []:
#             formatted[db_obj.id] = skipped_fields

#         # Collect all contracts into a list
#         contract_values = [
#             cast(str, v[:255])
#             for i, _ in enumerate(contract_columns)
#             if (n := f"contract{i}") in customer_dict
#             and isinstance(v := customer_dict[n], str)
#         ]

#         # If we have to add contracts from link, we need to push
#         # and receive customer's id
#         if contract_values != []:
#             db.commit()
#             db.refresh(db_obj)
#         for contract in contract_values:
#             crud.contract.create(
#                 db,
#                 obj_in=schemas.ContractCreate(owner_id=db_obj.id, orig_name=contract),
#                 commit=False,
#             )

#         if i % 100 == 0:
#             self.send_event(
#                 "task-update",
#                 data={"processed": i, "total": len(df), "formatted": formatted},
#             )
#     db.commit()

#     storage.delete_file(filename)
#     return {
#         "info": "done",
#         "length": len(df),
#         "formatted": formatted,
#     }
