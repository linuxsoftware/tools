#!/bin/python2
# This utility will convert from MoinMoin wiki text to html

import sys
import os.path
from MoinMoin import log
log.logging_config = log.logging_config.replace("loglevel=INFO",
                                                "loglevel=ERROR")
from MoinMoin.parser.text_moin_wiki import Parser
from MoinMoin.formatter.text_html import Formatter
from MoinMoin.config.multiconfig import DefaultConfig
from MoinMoin.web.contexts import AllContext
from MoinMoin.web.request import TestRequest
from MoinMoin import i18n

class Config(DefaultConfig):
    url_prefix_static = "/yesteryears"
    theme_default     = "ls_stardust"
    def __init__(self, id):
        DefaultConfig.__init__(self, id)
    def  _check_directories(self):
        pass
    def _loadPluginModule(self):
        self._plugin_modules = []

class Page(object):
    def __init__(self):
        self.hilite_re = None
        self.page_name = "bliki"

class Context(AllContext):
    def __init__(self):
        req = TestRequest()
        req.given_config = Config
        AllContext.__init__(self, req)
        self.content_lang = self.current_lang = self.lang = "en"
        self.session=None
        i18n.i18n_init(self)

    def convert(self, text):
        del self.response[:]
        formatter = Formatter(self)
        formatter.setPage(Page())
        Parser(text, self).format(formatter)
        html = "".join(self.response)
        return html

def main():
    context = Context()
    for wikiFname in sys.argv[1:]:
        with open(wikiFname) as f:
            text = f.read()
        htmlFname = os.path.splitext(wikiFname)[0] + ".html"
        print(htmlFname)
        with open(htmlFname, "wt") as f:
            f.write(context.convert(text))

if __name__ == "__main__":
    main()
