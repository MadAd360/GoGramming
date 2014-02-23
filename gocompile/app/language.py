class Language(object):

    def __init__(self, type):
	self.type = type

    def getType(self):
        return self.type

    def getCompile(self):
	#This should return a string which will compile the code
        raise NotImplementedError("Not implemented")

    def getRun(self):
        #This should return a string which will run the code
        raise NotImplementedError("Not implemented")

    def getSyntax(self):
        #This should return a string which will call the correct CodeMirror highlighting
        raise NotImplementedError("Not implemented")

    def __str__(self):
        return "%s" % (self.type)
