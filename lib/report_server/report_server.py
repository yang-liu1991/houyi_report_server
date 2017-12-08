#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
Author: liuyang@xxx.cn
Created Time: 2017-10-20 14:35:41
"""

import os
import sys
import time
import logging
import threading
from report_working import ReportWorking
from django.conf import settings
from houyi_base import HouyiBase
from multiprocessing import cpu_count


class ReportServer(HouyiBase):
    def __init__(self):
        super(ReportServer, self).__init__()
        self.date       = time.strftime('%Y%m%d', time.localtime(time.time()))
        self.amazon_api     = ''
        self.logger		= logging.getLogger('report_server_info')
        self.wflogger	= logging.getLogger('report_server_wf')



    '''
    生成一个月之内的日期列表，依次获取数据
    '''
    def __get_date_list(self):
        date_list = []
        for i in range(0, 30):
            date = time.strftime("%Y%m%d", time.localtime(time.time() - 24 * 3600 * i))
            date_list.append(date)
        return date_list



    '''
    提交生成报表的任务
    '''
    def submit_amazon_report(self, report_date, record_type):
        try:
            amazon_report_info = self.amazon_api.set_amazon_report(report_date, record_type)
            if amazon_report_info:
                self.logger.info('[submit_amazon_report] Success, record_type:%s, report_date:%s, report_info:%s' % \
                    (record_type, report_date, amazon_report_info))
                return amazon_report_info
            raise Exception(amazon_report_info)
        except Exception as e:
            self.wflogger.exception('[submit_amazon_report] Exception, record_type:%s, report_date:%s' % \
                (record_type, report_date))
            return {}



    '''
    定时请求Report接口，将Report id等信息加入到Redis队列
    '''
    def add_queue_message(self):
        while True:
            try:
                amazon_profiles = self.get_amazon_profiles()
                for amazon_profile in amazon_profiles:
                    user_id         = amazon_profile["user_id"]
                    profile_id      = amazon_profile["profileId"]

                    try:
                        access_token = self.get_access_token(user_id, profile_id)
                        if not access_token:
                            raise Exception('Get access_token failed, user_id:%s, profile_id:%s' % (user_id, str(profile_id)))
                        self.amazon_api = self.init_amazon_api(access_token, str(profile_id))
                        if not self.amazon_api:
                            raise Exception('Amazon API Init Failed, user_id:%s, profile_id:%s, access_token:%s' % \
                                (user_id, str(profile_id), access_token))
                    except Exception as e:
                        self.wflogger.exception('[add_queue_message] Exception, reason:%s' % (e))
                        continue

                    report_date_list = self.__get_date_list()
                    for report_date in report_date_list:
                        record_type_list = ['campaigns', 'adGroups', 'keywords', 'productAds']
                        for record_type in record_type_list:
                            report_info = {}
                            report_request = self.submit_amazon_report(report_date, record_type)
                            # The status of the generation of the report, it can be IN_PROGRESS, SUCCESS or FAILURE
                            if "status" in report_request and report_request["status"] != 'FAILURE':
                                report_info.update(report_request)
                                report_info.update({'accessToken':access_token, 'profileId':profile_id, 'userId':user_id, "reportDate":report_date})
                                self.redis.lpush('report_queue', report_info)
                                self.logger.info('[add_queue_message] Success, report_info:%s' % (report_info))
                #休息200秒
                time.sleep(settings.REPORT_INTERVAL)
            except Exception as e:
                self.wflogger.exception('[add_queue_message] Exception, reason:%s' % (e))



    '''
    Report Server控制方法
    '''
    def run(self):
        try:
            self.logger.info('Report Server starting...')

            add_message_thread = threading.Thread(target=self.add_queue_message)
            add_message_thread.setDaemon(True)
            add_message_thread.start()
            self.logger.info('Add Message Thread starting...')


            report_thread_list = []
            for report_thread_num in range(cpu_count()):
                thread_working = ReportWorking(self)
                report_thread_list.append(thread_working)

            for report_thread_working in report_thread_list:
                report_thread_working.setDaemon(True)
                report_thread_working.start()

            for report_thread_working in report_thread_list:
                report_thread_working.join()
            print 'Bye bye!'
        except Exception as e:
            self.wflogger.exception('Report Server Exception, reson:%s, system exit!' % e)
            sys.exit(1)





# vim: set noexpandtab ts=4 sts=4 sw=4 :
