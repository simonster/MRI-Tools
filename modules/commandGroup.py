# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 14:52:23 2011

@author: simon
"""

import subprocess

class CommandGroup:
    def __init__(self, cmd=None):
        self.popens = []
        self.argLists = []
        
        if cmd:
            self.run(cmd)
            self.wait()
    def run(self, args):
        popen = subprocess.Popen(args)
        self.popens.append(popen)
        self.argLists.append(args)
    def wait(self):
        for popen, argList in zip(self.popens, self.argLists):
            popen.wait()
            if popen.returncode != 0:
                raise subprocess.CalledProcessError(popen.returncode, argList)