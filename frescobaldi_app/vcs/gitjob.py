import os
import re
import time
import functools

from PyQt5.QtCore import QProcess, pyqtSignal



class GitError(Exception):
    pass

class Git():
    done = pyqtSignal(bool)

    def __init__(self, workingdirectory = None):
        self._executable = None
        self._executable = self._executable if self._executable else 'git'
        self._workingdirectory = workingdirectory
        self._queue = []
        self._version = None

    def run(self, args, receiver, isbinary = False):
        unit = {}
        
        process = QProcess()
        process.setProgram(self._executable)
        process.setArguments(args)
        process.setWorkingDirectory(self._workingdirectory)
        process.finished.connect(functools.partial(self._handleResult, isbinary))
        
        unit['process'] = process
        unit['receiver'] = receiver
        self._queue.append(unit)
        
        process = None
        unit = None
 
        if len(self._queue) == 1:
            self._queue[0]['process'].start()

    def run_blocking(self, args, isbinary = False):
        """
        """
        process = QProcess()
        process.setWorkingDirectory(self._workingdirectory)
        process.start(self._executable, args)
        process.waitForFinished()
        stderr = str(process.readAllStandardError(), 'utf-8')
        if stderr:
            raise GitError(stderr)
        else:
            if isbinary:
                return process.readAllStandardOutput()
            stdout = str(process.readAllStandardOutput(), 'utf-8').split('\n')
            if not stdout[-1]:
                stdout.pop()
            return stdout


    def _handleResult(self, isbinary):
        """
        """
        stderr = str(self._queue[0]['process'].readAllStandardError(), 'utf-8')
        if stderr:
            raise GitError(stderr)
        else:
            if isbinary:
                stdout = self._queue[0]['process'].readAllStandardOutput()
            else:
                stdout = str(self._queue[0]['process'].readAllStandardOutput(), 'utf-8').split('\n')
                if not stdout[-1]:
                    stdout.pop()
            self._queue[0]['receiver'](stdout)
        del self._queue[0]
        if self._queue:
            self._queue[0]['process'].start()    

    def setWorkingDirectory(self, workingdirectory):
        self._workingdirectory = workingdirectory

    def workingDirectory(self):
        return self._workingdirectory

    def setGitExecutable(self, executable):
        self._executable = executable

    def gitExecutable(self):
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

    def _tic(self):
        """
        Helper function to count how much time a git command takes
        """
        self._timer = time.perf_counter()

    def _toc(self, args = []):
        """
        Helper function to count how much time a git command takes
        """
        if self._timer:
            print('command git {} takes {}'.format(' '.join(args), 
                time.perf_counter()-self._timer))
            self._timer = None


    def version(self):
        """
        Return git executable version.

        The version string is used to check, whether git executable exists and
        works properly. It may also be used to enable functions with newer git
        versions.

        Returns:
            tuple: PEP-440 conform git version (major, minor, patch)
        """
        args = ['--version']
        # Query git version synchronously
        output = self.run_blocking(args) or ''
        # Parse version string like (git version 2.12.2.windows.1)
        match = re.match(r'git version (\d+)\.(\d+)\.(\d+)', output[0])
        if match:
            # PEP-440 conform git version (major, minor, patch)
            self._version = tuple(int(g) for g in match.groups())
            return self._version







