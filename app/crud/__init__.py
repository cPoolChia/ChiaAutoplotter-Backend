from .base import CRUDBase
from .user import CRUDUser
from .server import CRUDServer
from .plot import CRUDPlot
from .plot_queue import CRUDPlotQueue
from .directory import CRUDDirectory
from .transfer import CRUDTransfer

user = CRUDUser()
server = CRUDServer()
plot = CRUDPlot()
plot_queue = CRUDPlotQueue()
directory = CRUDDirectory()
transfer = CRUDTransfer()