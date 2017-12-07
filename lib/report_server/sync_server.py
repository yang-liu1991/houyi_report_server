#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
Author: liuyang@domob.cn
Created Time: 2017-10-23 14:35:41
"""

import os
import sys
import time
import logging
import redis
import threading
from django.conf import settings
from pymongo import MongoClient
from sync_working import SyncWorking
from houyi_base import HouyiBase
from multiprocessing import cpu_count


class SyncServer(HouyiBase):
    def __init__(self):
        super(SyncServer, self).__init__()
        self.date = time.strftime('%Y%m%d', time.localtime(time.time()))
        self.access_token = ''
        self.amazon_api = ''
        self.logger     = logging.getLogger('syncing_server_info')
        self.wflogger   = logging.getLogger('syncing_server_wf')

        # 初始化Redis
        redis_pool = redis.ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
        self.redis = redis.StrictRedis(connection_pool=redis_pool)

        # 初始化Mongo DB
        self.mclient = MongoClient(settings.M_HOST, settings.M_PORT)



    '''
    定时请求snapshots接口，将Request id等信息加入到Redis队列
    '''
    def add_queue_message(self):
        while True:
            try:
                amazon_profiles = self.get_amazon_profiles()
                for amazon_profile in amazon_profiles:
                    user_id = amazon_profile["user_id"]
                    profile_id = amazon_profile["profileId"]

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

                    record_type_list = ['campaigns', 'adGroups', 'keywords', 'productAds']
                    amazon_profile.pop('_id')
                    for record_type in record_type_list:
                        syncing_info = {"recordType":record_type, "accessToken":access_token, 'profileInfo':amazon_profile}
                        self.redis.lpush('syncing_queue', syncing_info)
                        self.logger.info('[add_queue_message] Success, record_type:%s, syncing_info:%s' % \
                            (record_type, syncing_info))
                # 休息200秒
                time.sleep(settings.SYNCING_INTERVAL)
            except Exception as e:
                self.wflogger.exception('[add_queue_message] Exception, reason:%s' % (e))


    '''
    同步模块控制方法
    '''
    def run(self):
        try:
            self.logger.info('Syncing Server starting...')

            add_message_thread = threading.Thread(target=self.add_queue_message)
            add_message_thread.setDaemon(True)
            add_message_thread.start()
            self.logger.info('Add Message Thread starting...')

            report_thread_list = []
            for report_thread_num in range(cpu_count()):
                thread_working = SyncWorking(self)
                report_thread_list.append(thread_working)

            for report_thread_working in report_thread_list:
                report_thread_working.setDaemon(True)
                report_thread_working.start()

            for report_thread_working in report_thread_list:
                report_thread_working.join()
            print 'Bye bye!'
        except Exception as e:
            self.wflogger.exception('Sync Server Exception, reson:%s, system exit!' % e)
            sys.exit(1)



