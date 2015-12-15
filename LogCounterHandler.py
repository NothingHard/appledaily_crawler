import logging


class LogCounterHandler(logging.Handler):
    def __init__(self, level=logging.WARN):
        super(LogCounterHandler, self).__init__()
        self.setLevel(level)
        self.logCount = 0
        self.dictLog = {}

    def flush(self):
        pass

    def emit(self, record):
        try:
            self.logCount +=1
            #msg = self.format(record)
            value = 1
            if (record.levelno in self.dictLog):
                value = self.dictLog[record.levelno] + 1
            self.dictLog[record.levelno] = value

        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


    def reportByLevel(self, level):
        return self.dictLog[level] if level in self.dictLog else 0

    def report(self):
        msg=""
        for level in range(0,60,10):
            if level >= self.level:
                msg+="%s: %d\r\n" % (logging.getLevelName(level), self.reportByLevel(level))

        return msg