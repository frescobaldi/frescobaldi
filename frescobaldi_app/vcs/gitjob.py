from PyQt5.QtCore import QProcess, pyqtSignal
import os

class Git():
    done = pyqtSignal(bool)

    def __init__(self, workingdirectory):
        self._executable = 'git'
        self._workingdirectory = workingdirectory
        self._queue = []

    def run(self, args, receiver):
        unit = {}
        
        p = QProcess()
        p.setProgram(self._executable)
        p.setArguments(args)
        p.setWorkingDirectory(self._workingdirectory)
        p.finished.connect(self._handleResult)
        
        unit['process'] = p
        unit['receiver'] = receiver
        self._queue.append(unit)
        
        p = None
        unit = None
 
        if len(self._queue) == 1:
            self._queue[0]['process'].start()

    def _handleResult(self):
        output = ''
        output = self._queue[0]['process'].readAllStandardOutput()
        if output != '':
            self._queue[0]['receiver'](output) 
        
        del self._queue[0]
        if self._queue:
            self._queue[0]['process'].start()
   
    def setWorkingDirectory(self, workingdirectory):
        self._workingdirectory = workingdirectory

    def workingDirectory(self, workingdirectory):
        return self._workingdirectory

    def setGitExecutable(self, executable):
        self._executable = executable

    def gitExecutable(self, executable):
        return self._executable

    def killCurrent(self):
        if self.isRunning():
            self._queue[0]['process'].finished.disconnect()
            # termination should be sync? 
            if os.name == "nt":
                self._queue[0]['process'].kill()
            else:
                self._queue[0]['process'].terminate()
            del self._queue[0]
    
    def killAll(self):
        self.killCurrent()
        self._queue = []
        
    def isRunning(self):
        return len(self._queue) > 0  








