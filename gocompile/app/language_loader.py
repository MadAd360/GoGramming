import pkgutil
import sys
from plugins import *
from language import Language
from app import models, db
import os
from flask import flash


def loadLanguages(dirname):
    module = "test"
    modules = pkgutil.iter_modules([dirname])
    #for file, pathname, description in imp.find_module(dirname):
    for importer, package_name, ispkg in modules:
    #for package_name in plugins.__all__:
	module = None
	full_package_name = '%s.%s' % (dirname, package_name)
	#if full_package_name not in sys.modules:
        #    module = importer.find_module(package_name
        #                ).load_module(full_package_name)
        #else:
	module = sys.modules[full_package_name]
	languages = classesinmodule(module)
        for lang in languages:
	    language = lang()
	    exist = models.Language.query.filter_by(filetype=language.getType()).first()
            if exist is None:
	    	db_lang = models.Language(filetype=language.getType(), compile=language.getCompile(), run=language.getRun(), syntax=language.getSyntax())
	    	db.session.add(db_lang)
    	db.session.commit()
    return module

def classesinmodule(module):
    md = module.__dict__
    return [
        md[c] for c in md if (
            isinstance(md[c], type) and md[c].__module__ == module.__name__ and issubclass(md[c], Language)
        )
    ]

