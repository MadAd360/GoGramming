from app import language
import plugins

class Java(language.Language):

    def __init__(self):
	language.Language.__init__(self, "java")

    def getCompile(self):
        return "javac "

    def getRun(self):
        return "java "

    def getSyntax(self):
        return "text/x-java"
