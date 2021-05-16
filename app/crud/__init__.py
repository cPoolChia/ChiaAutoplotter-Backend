from .base import CRUDBase
from .user import CRUDUser
from .server import CRUDServer
from .plot import CRUDPlot

user = CRUDUser()
server = CRUDServer()
plot = CRUDPlot()