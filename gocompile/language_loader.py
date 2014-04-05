#!./flask/bin/python

import pkgutil
import sys
from plugins import *
from app import models, db
from plugins import language
import os

def classesinmodule(module):
    md = module.__dict__
    return [
        md[c] for c in md if (
            isinstance(md[c], type) and md[c].__module__ == module.__name__ and issubclass(md[c], language.Language)
        )
    ]


languages = models.Language.query.all()
for lang in languages:
    db.session.delete(lang)
db.session.commit()



dirname = 'plugins'
modules = pkgutil.iter_modules([dirname])
for importer, package_name, ispkg in modules:
    if package_name != 'language':
    	module = None
    	full_package_name = '%s.%s' % (dirname, package_name)
    	module = sys.modules[full_package_name]
    	languages = classesinmodule(module)
    	for lang in languages:
	    print lang
	    prog = lang()
	    exist = models.Language.query.filter_by(filetype=prog.getType()).first()
            if exist is None:
	    	db_lang = models.Language(modulename=full_package_name, filetype=prog.getType(), interpreted=prog.getIfInterpreted(), additiondir=prog.getIfAdditionDir(), syntax=prog.getSyntax())
	    	db.session.add(db_lang)
db.session.commit()


