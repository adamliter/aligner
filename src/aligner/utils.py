import logging


def set_class_log_level(cls, level):
    levels = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG}
    cls.logger.setLevel(levels[level])
