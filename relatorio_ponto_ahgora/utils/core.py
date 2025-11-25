from utils.services import Services
from utils.file import UtilsFile
from utils.selenium import UtilsSelenium
from utils.log import UtilsLog

class Utils:
    def __init__(self, debug=False):
        self.debug = debug
        self.log = UtilsLog()
        self.file = UtilsFile(self.log, self.debug)
        self.service = Services(self.log)
        self.selenium = UtilsSelenium(self.log, self.debug)

    

