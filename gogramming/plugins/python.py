import language
import plugins

class Python(language.Language):

    def __init__(self):
	language.Language.__init__(self, "py")

    def getIfInterpreted(self):
        return True

    def getIfAdditionDir(self):
        return True

    def getCompile(self, filepath, location, additional, newname):
        return ""

    def getRun(self, filename):
        return self.pythonroot + " " + filename + ".py"

    def getSyntax(self):
        return "text/x-python"
