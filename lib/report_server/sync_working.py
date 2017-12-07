#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
Author: liuyang@domob.cn
Created Time: 2017-10-23 17:35:41
"""



import os
import sys
import json
import time
import datetime
import logging
import redis
import commands
import threading
from django.conf import settings
from amazon_advertising_api.amazon_advertising_api import AmazonAdvertisingApi


class SyncWorking(threading.Thread):
    def __init__(self, sync_server, **kwargs):
        threading.Thread.__init__(self, **kwargs)
        self.redis          = sync_server.redis
        # 初始化Mongo DB
        self.db             = sync_server.db
        self.date           = sync_server.date
        self.date_hr        = sync_server.date_hr
        self.logger         = sync_server.logger
        self.wflogger       = sync_server.wflogger
        self.amazon_api     = sync_server.amazon_api
        self.parent         = sync_server



    '''
    初始化Amazon Api
    '''
    def __init_amazon_api(self, access_token, profile_id):
        try:
            amazon_api = AmazonAdvertisingApi(access_token, profile_id)
            return amazon_api
        except Exception as e:
            self.wflogger.exception('[__init_amazon_api] Exception, access_token:%s, profile_id:%s. reason:%s' % \
                (access_token, profile_id, e))
            return False


    '''
    获取相应extended数据
    '''
    def __get_amazon_extended(self, record_type):
        try:
            if record_type == 'campaigns':
                amazon_extended = self.amazon_api.get_amazon_campaigns()
            elif record_type == 'adGroups':
                amazon_extended = self.amazon_api.get_amazon_adgroups()
            elif record_type == 'productAds':
                amazon_extended = self.amazon_api.get_amazon_productads()
            else:
                raise Exception('Unknow record_type')

            if "status" not in amazon_extended:
                self.logger.info('[__get_amazon_extended] Exception, record_type:%s amazon_extend:%s' % \
                    (record_type, amazon_extended))
                return amazon_extended
            raise Exception(amazon_extended)
        except Exception as e:
            self.wflogger.exception('[__get_amazon_extended] Exception, record_type:%s. reason:%s' % \
                (record_type, e))
            return False



    '''
    获取所有adgroups数据，用于获取单独的keywords信息
    '''
    def __get_amazon_adgroups(self):
        adgroup_list = []
        try:
            collection = self.db.adgroup_info
            adgroups_info = collection.find()
            if adgroups_info:
                for adgroup in adgroups_info:
                    adgroup_list.append({"campaignId":adgroup["campaignId"], "adGroupId":adgroup["adGroupId"]})
                self.logger.info('[__get_amazon_adgroups] Success, adgroup_list:%s' % adgroup_list)
                return adgroup_list
            raise Exception(adgroups_info)
        except Exception as e:
            self.wflogger.exception('[__get_amazon_adgroups] Exception, reason:%s' % (e))
            return adgroup_list



    '''
    按照campaignId和adGroupId获取相应keywords信息
    '''
    def __get_amazon_keywords(self, campaign_id, adgroup_id):
        try:
            params = {"campaignIdFilter":campaign_id, "adGroupIdFilter":adgroup_id}
            amazon_keywords = self.amazon_api.get_amazon_keywords(params)
            if "code" not in amazon_keywords:
                for amazon_keyword in amazon_keywords:
                    if "bid" in amazon_keyword: amazon_keyword["bid"] = int(float(amazon_keyword["bid"]) * 1000000)
                self.logger.info('[__get_amazon_keywords] Success, campaign_id:%s, adgroup_id:%s, amazon_keywords:%s' % \
                    (str(campaign_id), str(adgroup_id), amazon_keywords))
                return amazon_keywords
            raise Exception(amazon_keywords)
        except Exception as e:
            self.wflogger.exception('[__get_amazon_keywords] Exception, campaign_id:%s, adgroup_id:%s, reason:%s' % \
                (str(campaign_id), str(adgroup_id), e))
            return []


    '''
    将返回的数据重组，将涉及金额的，全部*1000000
    '''
    def __build_amazon_extended(self, amazon_extended_info, syncing_info):
        save_syncing_data_list = []
        try:
            if amazon_extended_info:
                for amazon_extend_data in amazon_extended_info:
                    save_syncing_data = {}
                    # dailyBudget
                    if "dailyBudget" in amazon_extend_data:
                        amazon_extend_data["dailyBudget"] = int(amazon_extend_data["dailyBudget"]) * 1000000
                    # Bid
                    if "defaultBid" in amazon_extend_data:
                        amazon_extend_data["defaultBid"] = int(float(amazon_extend_data["defaultBid"]) * 1000000)
                    save_syncing_data.update(amazon_extend_data)
                    save_syncing_data.update(syncing_info)
                    save_syncing_data_list.append(save_syncing_data)
            self.logger.info('[__build_amazon_extended] Info, amazon_extended_info:%s, syncing_info:%s, save_syncing_data_list:%s' % \
                    (amazon_extended_info, syncing_info, save_syncing_data_list))
            return save_syncing_data_list
        except Exception as e:
            self.wflogger.exception('[__build_amazon_extended] Exception, amazon_extended_info:%s, syncing_info:%s, reason:%s' % \
                (amazon_extended_info, syncing_info, e))
            return []


    '''
    构建keywords的保存数据
    '''
    def __build_keywords_syncing(self, adgroup, syncing_info):
        save_syncing_data = {}
        try:
            keyword_list = self.__get_amazon_keywords(adgroup["campaignId"], adgroup["adGroupId"])
            # 如果keyword数据为空，则忽略
            if not keyword_list: return False
            save_syncing_data.update({
                "adGroupId": adgroup["adGroupId"],
                "campaignId": adgroup["campaignId"],
                "userId": syncing_info["profileInfo"]["user_id"],
                "keywordList": keyword_list
            })

            save_syncing_data.update(syncing_info)
            self.logger.info('[__build_keywords_syncing] Success, adgroup:%s, syncing_info:%s, save_syncing_data:%s' % \
                (adgroup, syncing_info, save_syncing_data))
            return save_syncing_data
        except Exception as e:
            self.wflogger.exception('[__build_keywords_syncing] Exception, adgroup:%s, syncing_info:%s' % \
                (adgroup, syncing_info))
            return False


    '''
    保存同步数据
    '''
    def __save_syncing_data(self, save_syncing_data):
        try:
            # 如果返回的为adgroup数据
            if save_syncing_data['recordType'].lower() == 'adgroups':
                collection = self.db.adgroup_info
                query = {"adGroupId":int(save_syncing_data["adGroupId"])}
            # 返回keyword数据
            elif save_syncing_data['recordType'].lower() == 'keywords':
                collection = self.db.keyword_info
                query = {
                    "campaignId":int(save_syncing_data["campaignId"]),
                    "adGroupId":int(save_syncing_data["adGroupId"])
                }
            # 返回campaign数据
            elif save_syncing_data['recordType'].lower() == 'campaigns':
                collection = self.db.campaign_info
                query = {"campaignId":int(save_syncing_data["campaignId"])}
            # 返回product ad数据
            elif save_syncing_data['recordType'].lower() == 'productads':
                collection = self.db.productad_info
                query = {"adId":int(save_syncing_data["adId"])}
            # 返回脑残数据
            else:
                raise Exception('Unknow record_type!')
            save_syncing_data.pop('recordType')
            result = collection.update(query, save_syncing_data, True, False)
            if result:
                self.logger.info('[__save_syncing_data] Success, save_syncing_data:%s, result:%s' % \
                    (save_syncing_data, result))
                return result
            raise Exception('Syncing Server Insert Failed, result:%s' % result)
        except Exception as e:
            self.wflogger.exception('[__save_syncing_data] Exception, save_syncing_data:%s, reason:%s' % \
                (save_syncing_data, e))
            return False



    '''
    同步逻辑执行方法
    '''
    def run(self):
        while True:
            try:
                queue_syncing_info = self.redis.lpop('syncing_queue')
                if queue_syncing_info:
                    syncing_info = eval(queue_syncing_info)

                    self.logger.info('[sync_working_run] Info, syncing_info:%s' % syncing_info)
                    access_token    = syncing_info['accessToken']
                    record_type     = syncing_info["recordType"]
                    profileInfo     = syncing_info["profileInfo"]
                    profile_id      = int(profileInfo["profileId"])
                    user_id         = str(profileInfo["user_id"])

                    try:
                        access_token = self.parent.get_access_token(user_id, profile_id)
                        self.amazon_api = self.__init_amazon_api(access_token, profile_id)
                    except Exception as e:
                        self.wflogger.exception(
                            '[report_working_run] Exception, access_token:%s, reason:%s' % (access_token, e))
                        continue
                    syncing_info.pop('accessToken')

                    if "profileInfo" in syncing_info:
                        profileInfo = syncing_info["profileInfo"]
                        if "dailyBudget" in profileInfo:
                            profileInfo["dailyBudget"] = int(profileInfo["dailyBudget"]) * 1000000
                        syncing_info["profileInfo"] = profileInfo

                    # 如果record_type类型为keywords，keywords的表结构与其他的有区别
                    if record_type.lower() == 'keywords':
                        adgroup_list = self.__get_amazon_adgroups()
                        for adgroup in adgroup_list:
                            save_syncing_data = self.__build_keywords_syncing(adgroup, syncing_info)
                            if not save_syncing_data: continue
                            self.__save_syncing_data(save_syncing_data)
                    # record_type为campaign、adgroup 、product ads
                    else:
                        amazon_extended_info = self.__get_amazon_extended(record_type)
                        if amazon_extended_info:
                            save_syncing_data_list = self.__build_amazon_extended(amazon_extended_info, syncing_info)
                            for save_syncing_data in save_syncing_data_list:
                                self.__save_syncing_data(save_syncing_data)
            except Exception as e:
                self.wflogger.exception('[SyncWorking] Exception, reason:%s' % e)
                sys.exit(1)