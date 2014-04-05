import language
import plugins

class C(language.Language):

    def __init__(self):
	language.Language.__init__(self, "c")

    def getIfInterpreted(self):
        return False

    def getIfAdditionDir(self):
        return False

    def getCompile(self, filepath, location, additional, newname):
        if filepath is not None and location is not None and newname is not None:
            basic = "gcc " + filepath
	    newlocation = " -o " + location + "/" + newname
            if additional is not None:
                other = " "
                for line in additional:
                    other = other + line + " "
                return basic + other + newlocation
            else:
                return basic + newlocation
        else:
            return None


    def getRun(self, filename):
        return "./" + filename

    def getSyntax(self):
        return "text/x-csrc"
