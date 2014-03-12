import os

class Language(object):

    def __init__(self, type):
	self.type = type
	self.resourceroot = os.path.dirname(os.path.abspath(__file__)) + "/plugin-resources"
	self.pythonroot = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0] + "/flask/bin/python"

    def getType(self):
        return self.type

    def getIfInterpreted(self):
        #This should return a boolena which will state whether the language is interpreted or not
        raise NotImplementedError("Not implemented")

    def getCompile(self):
	#This should return a string which will compile the code
        raise NotImplementedError("Not implemented")

    def getCompileLocation(self):
        #This should return a string which will state where the compiled code should be placed
        raise NotImplementedError("Not implemented")

    def getCompileIfFile(self):
        #This should return a boolean which will state whether the compiled location is a file (or a directory)
        raise NotImplementedError("Not implemented")

    def getRun(self):
        #This should return a string which will run the code
        raise NotImplementedError("Not implemented")

    def getIfIncludeType(self):
        #This should return a boolean to state whether the type must be included when run
        raise NotImplementedError("Not implemented")

    def getSyntax(self):
        #This should return a string which will call the correct CodeMirror highlighting
        raise NotImplementedError("Not implemented")

    def __str__(self):
        return "%s" % (self.type)
