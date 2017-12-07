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
import hashlib
import time
import random
import redis
from pymongo import MongoClient
from django.conf import settings
from amazon_advertising_api.amazon_advertising_api import AmazonAdvertisingApi

#thrift
from domob_pyutils.thriftext import TThriftClientPool
from domob_thrift.houyi_common_types.ttypes import *
from domob_thrift.houyi_info_server_types.ttypes import *
from domob_thrift.houyi_info_server_service import InfoServer




class HouyiBase(object):
    def __init__(self):
        self.date       = time.strftime('%Y%m%d', time.localtime(time.time()))
        self.date_hr    = time.strftime('%Y%m%d%H', time.localtime(time.time()))
        self.logger		= logging.getLogger('report_server_info')
        self.wflogger	= logging.getLogger('report_server_wf')
        self.access_token   = ''
        self.amazon_api     = ''

        #初始化Redis
        redis_pool		= redis.ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
        self.redis		= redis.StrictRedis(connection_pool=redis_pool)

        #初始化Mongo DB
        if settings.DEBUG:
            mongo_url       = 'mongodb://%s:%d' % (
                settings.M_HOST,
                settings.M_PORT,
            )
        else:
            mongo_url       = 'mongodb://%s:%s@%s/%s' % (
                settings.M_USER,
                settings.M_PASS,
                settings.M_HOST,
                settings.M_NAME)
        self.client         = MongoClient(mongo_url)
        self.db             = self.client[settings.M_NAME]

        self.infoServerPool = TThriftClientPool.TThriftClientPool(
            InfoServer.Client,
            settings.INFO_HOST,
            settings.INFO_PORT,
            settings.INFO_SIZE
        )



    '''
    初始化Amazon Api
    '''
    def init_amazon_api(self, access_token, scope):
        try:
            amazon_api = AmazonAdvertisingApi(access_token, scope)
            return amazon_api
        except Exception as e:
            self.wflogger.exception('[init_amazon_api] Exception, access_token:%s, scope:%s, reason:%s' % \
                (access_token, str(scope), e))
            return False


    '''
    获取search Id
    '''
    def __get_search_id(self):
        rand_time = time.time() + random.randint(0, 10 ** 6)
        tmp_res = hashlib.md5(str(rand_time))
        res = tmp_res.hexdigest()
        as_int = int(res, 16)
        return int(str(as_int)[0:15])



    '''
    获取Amazon profiles信息
    '''
    def get_amazon_profiles(self):
        amazon_profile_list = []
        try:
            collection = self.db.profile_info
            amazon_profiles = collection.find()
            if amazon_profiles:
                for amazon_profile in amazon_profiles:
                    amazon_profile_list.append(amazon_profile)
                self.logger.info('[get_amazon_profiles] Success, amazon_profile_list:%s' % (amazon_profile_list))
                return amazon_profile_list
            raise Exception('Not found amazon profiles!')
        except Exception as e:
            self.wflogger.exception('[get_amazon_profiles] Exception, reason:%s' % (e))
            return []



    '''
    获取Amazon AccessToken
    '''
    def get_access_token(self, user_id, profile_id):
        try:
            search_id = self.__get_search_id()
            header = ReqHeader()
            header.searchId     = search_id
            header.userId       = user_id
            header.profileId    = profile_id

            access_token_response = GetAccessTokenResp()
            access_token_response.respHeader = header

            with self.infoServerPool.get() as client:
                client.setRetry(3)
                response = client.getAccessToken(header)
            self.logger.info('[get_access_token] Info, user_id:%s, profile_id:%s, response:%s' % \
                (user_id, profile_id, response))
            return response.token
        except Exception as e:
            self.wflogger.exception('[get_access_token] Exception, user_id:%s, profile_id:%s, reason:%s' %
                (user_id, profile_id, e))
            return ''

