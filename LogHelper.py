#coding: utf-8
import logging
import os
import traceback


class LogHelper:
    LoggerName=__name__
    # def __init__(self, logger):
    #     self.logger=logger
    #
    # def d(self, text):
    #     self.logger.debug(text)
    #
    # def e(self, text):
    #     self.logger.error(text)
    #
    # def i(self, text):
    #     self.logger.info(text)
    #
    # def w(self, text):
    #     self.logger.warn(text)

    # def print_exceptionXXX(self, ex, msg=None):
    # trace = traceback.format_exc()
    # self.logger.exception(trace)
    # self.logger.exception("*"+str(ex))
    #
    # self.logger.exception("*"+msg)


    @staticmethod
    def getExceptionMsg(ex, msg):
        result = traceback.format_exc()
        result+=os.linesep+"*"+str(ex)
        if(msg):
            result+=os.linesep+"*"+msg
