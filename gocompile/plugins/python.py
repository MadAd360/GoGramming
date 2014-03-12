import language
import plugins

class Python(language.Language):

    def __init__(self):
	language.Language.__init__(self, "py")

    def getIfInterpreted(self):
        return True

    def getCompile(self):
        return ""

    def getCompileLocation(self):
        return ""

    def getCompileIfFile(self):
	return False

    def getRun(self):
        return self.pythonroot + " "

    def getIfIncludeType(self):
        return True

    def getSyntax(self):
        return "text/x-python"
