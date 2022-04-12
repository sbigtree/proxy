import logging
import os, stat
import sys

from log import log

sys.stderr = sys.stdout


# log配置，实现日志自动按日期生成日志文件

def make_dir(make_dir_path):
    path = make_dir_path.strip()
    if not os.path.exists(path):
        os.makedirs(path)
        os.chmod(path, stat.S_IRWXO + stat.S_IRWXG + stat.S_IRWXU)


def init_logger(dir_name='logs', log_file_name='log', debug=False, join='.', logger=log,
                file_level=logging.WARNING):
    """
    :param dir_name 文件夹名字
    :param join 拼接的目录，默认是os.getcwd()，传入.. 则是os.getcwd()的上一级目录
    """

    # print('日志级别', level)

    # level = logging.DEBUG
    # print('logger level is ',level)
    log_file_name = log_file_name + '.log'
    # os.pardir 输出为 ..
    log_file_folder = os.path.join(os.getcwd(), join, 'logs')
    # print('项目运行目录', os.getcwd())
    # make_dir(log_file_folder)

    log_file_folder = os.path.abspath(
        log_file_folder) + os.sep + dir_name

    # print('日志文件路径', log_file_folder)
    make_dir(log_file_folder)
    log_file_str = log_file_folder + os.sep + log_file_name

    '''如果是使用
    logging.basicConfig(level=logging.DEBUG)设置的话，那么使用app.logger打印的日志仍会不分等级均记录，
    而系统运行日志才会按照设置的等级进行记录。使用file_log_handler.setLevel(logging.WARNING)
    设置等级的话，那么不管是app.logger打印的日志还是系统运行日志均按照设置等级进行记录
    '''
    # 设置日志的格式                   发生时间    日志等级     日志信息文件名      函数名          行数        日志信息
    format_str = '%(asctime)s - %(filename)s - [line:%(lineno)s] - %(levelname)s: %(message)s'
    # 将日志记录器指定日志的格式
    formatter = logging.Formatter(format_str, datefmt=None)

    # 创建日志记录器，指明日志保存路径,每个日志的大小，保存日志的上限
    from logging.handlers import RotatingFileHandler
    file_log_handler = RotatingFileHandler(log_file_str, maxBytes=5 * 1024 * 1024, backupCount=10)
    # 日志等级的设置
    file_log_handler.setLevel(file_level)

    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象添加日志记录器
    # 默认日志等级的设置
    if debug:
        pass
        level = logging.INFO
        logger.setLevel(level)
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        # logging.basicConfig(level=level, format=format_str)

    logger.addHandler(file_log_handler)

    # coloredlogs.install(logger=logger, level=level, fmt=format_str, datefmt=None, milliseconds=True)
