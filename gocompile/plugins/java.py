import language
import plugins

class Java(language.Language):

    def __init__(self):
	language.Language.__init__(self, "java")

    def getIfInterpreted(self):
	return False

    def getIfAdditionDir(self):
	return True

    def getCompile(self, filepath, location, additional, newname):
	if filepath is not None and location is not None:
	    basic = "sudo javac " + filepath + " -d " + location
	    if additional is not None:
		other = ""
		for line in additional:
		    other = other + line + ":" 
		return basic + " -cp \'.:" + other + "\'" 
	    else:
		return basic		
	else:
	    return None

    def getRun(self, filename):
        return "java " + filename

    def getSyntax(self):
        return "text/x-java"

