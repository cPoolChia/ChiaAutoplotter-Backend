from app import crud, models, schemas
from app.api import deps
from fastapi import Depends
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from app.api.routes.base import BaseAuthCBV

router = InferringRouter()


@cbv(router)
class PlotCBV(BaseAuthCBV):
    @router.get("/")
    def get_plots_table(
        self,
        filtration: schemas.FilterData[models.Plot] = Depends(
            deps.get_filtration_data(models.Plot)
        ),
    ) -> schemas.Table[schemas.PlotReturn]:
        amount, items = crud.plot.get_multi(self.db, filtration=filtration)
        return schemas.Table[schemas.PlotReturn].from_orm(amount=amount, items=items)
