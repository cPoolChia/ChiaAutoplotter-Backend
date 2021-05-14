from typing import Any, Dict, Optional, Union
from uuid import UUID

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from sqlalchemy.orm import Session


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_nickname(self, db: Session, *, nickname: str) -> Optional[User]:
        return db.query(self.model).filter(self.model.nickname == nickname).first()

    def create(self, db: Session, *, obj_in: UserCreate, commit: bool = True) -> User:
        obj_dict = obj_in.dict()
        obj_dict["hashed_password"] = get_password_hash(obj_in.password)
        del obj_dict["password"]
        db_obj = User(**obj_dict)
        db.add(db_obj)
        if commit:
            db.commit()
            db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        update_data = {"password": None} | (
            obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
        )

        if update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data["password"])
        del update_data["password"]

        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, login: str, password: str) -> Optional[User]:
        user = self.get_by_nickname(db, nickname=login)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
