import codecs
import logging
import os
import base64
import urllib
from LogHelper import LogHelper

__author__ = 'kevin'

logger = logging.getLogger(LogHelper.LoggerName)


class FileHelper:
    @staticmethod
    def read_last_line(filename):
        if not os.path.isfile(filename):
            return None
        with open(filename, 'rb') as fh:
            first = next(fh)
            offs = -100
            while True:
                fh.seek(offs, 2)
                lines = fh.readlines()
                if len(lines) > 1:
                    last = lines[-1]
                    return last
                offs *= 2

            #only one line
            fh.seek(0, 2)
            lines = fh.readlines()
            return lines[-1]

    @staticmethod
    def saveToFile(filename, data):
        file = None
        try:
            file = open(filename, mode='wb')
            file.write(data)
        except Exception as ex:
            logger.exception(LogHelper.getExceptionMsg(ex, "unable to save file: %s" % filename))
        finally:
            if (file != None):
                file.close()

    @staticmethod
    def saveTextToFile(filename, data, encoding="utf-8"):
        file = None
        try:
            file = codecs.open(filename, mode='w', encoding=encoding)
            #file = codecs.open(filename, mode='wb')
            #file = open(filename, mode='w')
            #file.write(u'\ufeff')  #codecs.BOM_UTF8
            file.write(data)
        except Exception as ex:
            logger.exception(LogHelper.getExceptionMsg(ex, "unable to save file: %s" % filename))
        finally:
            if (file != None):
                file.close()

    @staticmethod
    def getValidFilename(text):
        #return base64.urlsafe_b64encode(text)
        return urllib.quote_plus(text)