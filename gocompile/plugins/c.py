import language
import plugins

class C(language.Language):

    def __init__(self):
	language.Language.__init__(self, "c")

    def getIfInterpreted(self):
        return False

    def getCompile(self):
        return "gcc"

    def getCompileLocation(self):
        return "-o"

    def getCompileIfFile(self):
        return True

    def getRun(self):
        return "./"

    def getIfIncludeType(self):
        return False

    def getSyntax(self):
        return "text/x-csrc"
