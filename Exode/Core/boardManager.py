#   boardManager.py
#
#   boardManager manage the boards..
#
#   Created by Lenselle Nicolas, March, 2016.
#   lenselle.nicolas@gmail.com


# import to search port connected to a board
import itertools
import platform
from serial.tools import list_ports
if platform.system() == 'Windows':
    import _winreg as winreg
else:
    import glob

from .exode import *
from . import logCore

# Searching a port with Windows
def windows_ports():
    path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
    except WindowsError:
        raise Exception

    for i in itertools.count():
        try:
            val = winreg.EnumValue(key, i)
            yield (str(val[1]))  # , str(val[0]))
        except EnvironmentError:
            break


class BoardManager():

    def __init__(self):
        self.boardList= []

    def portUsed(self):
        return [board.portPath for board in self.boardList]

    def getBoardByPort(self, port):
        for board in self.boardList:
            if board.portPath == port:
                return board
        return None

    def add(self, board):
        board.id= len(self.boardList)
        board.name="Board-"+str(board.id)
        self.boardList.append(board)

    def searchBoard(self):
        #Return the 1st board founded with Exode installed
        logCore("Searching for a board...")

        #  Search a port
        if platform.system() == 'Windows':
            ports = windows_ports()
        elif platform.system() == 'Darwin':
            ports = [i[0] for i in list_ports.comports()]
        else:
            ports = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")

        for p in ports:
            try:
                logCore("Try to connect to :"+p)
                sr = serial.Serial(p, 9600)
            except (serial.serialutil.SerialException, OSError) as e:
                continue

            time.sleep(2)
            # This bit array execute the function checkExode()
            # on the board
            sr.write(bytearray([1, fct('checkExode')]))
            sr.flush()
            time.sleep(0.1)

            # the board should answer 202,404
            ans= [0,0]
            if sr.inWaiting()>0:
                ans[0] = int.from_bytes(sr.read(), byteorder='little')
                ans[1] = int.from_bytes(sr.read(4), byteorder='little', signed=False)

            logCore(p+" answered "+str(ans))
            if ans != [202,404]:
                continue
            else:
                logCore("Arduino board detected with Exode at : "+p)
                return Board(p)

        return None


    def autoAddObj(self, obj):
        # If there is only one board
        # add the obj (pin e.g) on the board
        if len(self.boardList) == 1:
            self.boardList[0].add(obj)

class Board(Exode):

    def __init__(self, port, name=""):

        if port not in BOARD_MANAGER.portUsed():

            self.portPath= port
            self.objLst= {}
            self.id = -1
            self.mute= False

            BOARD_MANAGER.add(self)
            if name != "":
                self.name= name
            Exode.__init__(self, port, self.name)
            logCore(self.name+" init at : "+self.portPath)

        else:
            self= BOARD_MANAGER.getBoardByPort(port)

    def add(self, obj):
        if(obj.board == None):
            obj.on(self)

    def addObject(self, name, values):
        if not name in self.objLst.keys():
            self.objLst[name]= []
        self.objLst[name].append(values)

    def __repr__(self):
        return self.name

BOARD_MANAGER= BoardManager()
#BOARD = BOARD_MANAGER.searchBoard()
