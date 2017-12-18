# -*- coding: utf8 -*-
# author：  咚咚呛
# 对主机的网络连接进行排查，当存在外部链接时，
# 且连接为差异变化时如增加，则进行日志记录

import os, sys, logging, subprocess, time

# 网络连接文件存储名称
NET_WORK_DB = sys.path[0] + '/network_db.txt'
# 日志告警文件存储位置
ALARM_LOG = '/var/log/network_check.log'


# 日志输出到指定文件，用于syslog同步服务器
def loging():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('NetWork Check')
    fh = logging.FileHandler(ALARM_LOG)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


# N个连续空格换为一个|
def replaceAll(old, new, str):
    while str.find(old) > -1:
        str = str.replace(old, new)
    while str.find(new + new) > -1:
        str = str.replace(new + new, new)
    return str


# 从记录库中得到历史远程ip记录
def get_history_remote_list():
    if not os.path.exists(NET_WORK_DB):
        os.mknod(NET_WORK_DB)
    history_remote_list = []
    for line in open(NET_WORK_DB):
        history_remote_list.append(line.split('\n')[0])
    return history_remote_list


# 重写远程连接库文件
def write_net_work_db(remote_list):
    try:
        if os.path.exists(NET_WORK_DB):
            os.remove(NET_WORK_DB)
            os.mknod(NET_WORK_DB)
        f = open(NET_WORK_DB, 'w')
        for remote_ip in remote_list:
            f.write(remote_ip + "\n")
        f.close()
    except:
        return


# 用ss命令导出导出本机
def check_network():
    try:
        # 获取网络连接内容，并过滤内网链接
        subproc = subprocess.Popen('cd ' + sys.path[
            0] + ' && sudo ss -nap4 not dst 192.168.0.1/16 and not dst 10.0.0.0/8 and not dst 127.0.0.1 and not dst 172.16.0.1/12 and dport \> :1',
                                   shell=True,
                                   stdout=subprocess.PIPE)
        (log, _) = subproc.communicate()
        # log 存储有所有外网连接字符串
        # 存储方式：tcp  ESTAB   0   0    172.16.0.2:6379    101.201.73.79:38739   users:(("redis-server",pid=13795,fd=152))
        # 替换连续的空格为一个|，好格式化数据
        res = replaceAll(' ', '|', log).split("\n")
        if len(res) > 1:
            # 得到历史远程ip记录
            history_remote_list = []
            # 表明本次结果是否存在差异变化
            Diff_IP = False

            # 得到历史远程ip记录
            history_remote_list = get_history_remote_list()

            for count in range(1, len(res) - 1):
                if res[count].split('|')[-2].find('.') > -1:
                    ip = res[count].split('|')[-2].split(':')[0]
                # 有可能存在进程取不到的现象
                elif res[count].split('|')[-1].find('.') > -1:
                    ip = res[count].split('|')[-1].split(':')[0]
                else:
                    continue
                # 判断远程连接是否在历史记录中
                if not ip in history_remote_list:
                    logger.info("%s " % res[count])
                    Diff_IP = True
                    history_remote_list.append(ip)
            if Diff_IP:
                # 更新存储库数据
                write_net_work_db(history_remote_list)
                # 为兼容syslog 最后一条日志不同步的现象
                logger.info("  ")
    except:
        return False


# 初始化日志接口
logger = loging()
if __name__ == '__main__':
    if sys.version_info < (2, 5):
        print "python version low"
        sys.exit()
    check_network()
