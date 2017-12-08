#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
Author: liuyang@xxx.cn
Created Time: 2017-10-19 12:07:51
"""

import os
import sys
import signal
import argparse
import datetime

from django.conf import settings


# 获取默认的运行时路径，并设置运行时需要加到sys.path的模块
exePath = os.path.realpath(os.path.dirname(__file__))
basepath = os.path.realpath(os.path.dirname(__file__) + '/../')
sys.path.append(exePath)


def quit(signum, frame):
    print 'You choose to stop me!'
    sys.exit(1)


if __name__ == '__main__':

    signal.signal(signal.SIGINT, quit)
    signal.signal(signal.SIGTERM, quit)

    # 命令行参数解析，默认解析'-d'，即指定该模块的运行时目录
    ap = argparse.ArgumentParser(description = 'houyi_report_server')
    ap.add_argument('-d', '--execute_dir', type = str, help = 'Houyi Server execute directory', default = basepath)
    ap.add_argument('-s', '--server', type = str, help='Houyi Server', default= 'reporting')
    args = ap.parse_args()
    print args
    print 'Run Houyi Report Server  at %s' % args.execute_dir
    os.chdir(args.execute_dir)
    # 加载配置
    print 'load django settings...'
    sys.path.append(os.path.join(args.execute_dir, "conf"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_settings")
    if settings.DEBUG:
        print "debug mode"

    if args.server == 'reporting':
        from report_server.report_server import ReportServer
        report_server = ReportServer()
        report_server.run()
    elif args.server == 'syncing':
        from report_server.sync_server import SyncServer
        syncing_server = SyncServer()
        syncing_server.run()
    else:
        print 'Bye bye!'






# vim: set noexpandtab ts=4 sts=4 sw=4 :
