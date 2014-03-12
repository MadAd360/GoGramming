import language
import plugins

class Java(language.Language):

    def __init__(self):
	language.Language.__init__(self, "java")

    def getIfInterpreted(self):
	return False

    def getCompile(self):
        return "javac"

    def getCompileLocation(self):
        return "-d"

    def getCompileIfFile(self):
	return False

    def getRun(self):
        return "java "

    def getIfIncludeType(self):
	return False

    def getSyntax(self):
        return "text/x-java"
