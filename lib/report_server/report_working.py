#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
Author: liuyang@xxx.cn
Created Time: 2017-10-20 14:35:41
"""

import os
import sys
import json
import time
import commands
import threading
from django.conf import settings
from amazon_advertising_api.amazon_advertising_api import AmazonAdvertisingApi


class ReportWorking(threading.Thread):
    def __init__(self, report_server, **kwargs):
        threading.Thread.__init__(self, **kwargs)
        self.redis          = report_server.redis
        # 初始化Mongo DB
        self.db             = report_server.db
        self.date           = report_server.date
        self.date_hr        = report_server.date_hr
        self.logger         = report_server.logger
        self.wflogger       = report_server.wflogger
        self.amazon_api     = report_server.amazon_api
        self.parent         = report_server



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
    获取报表状态
    '''
    def __get_amazon_report(self, report_id):
        try:
            amazon_report_info = self.amazon_api.get_amazon_report(report_id)
            if amazon_report_info:
                self.logger.info('[__get_amazon_report] Success, report_id:%s, date:%s, report_info:%s' % \
                    (report_id, self.date, amazon_report_info))
                return amazon_report_info
            raise Exception(amazon_report_info)
        except Exception as e:
            self.wflogger.exception('[__get_amazon_report] Exception, report_id:%s, date:%s, reason:%s' % \
                (report_id, self.date, e))
            return False


    '''
    获取AdGroup信息
    '''
    def __get_adgroup_by_id(self, adgroup_id):
        try:
            collection = self.db.adgroup_info
            adgroup_info = collection.find_one({"adGroupId":long(adgroup_id)})
            if adgroup_info:
                self.logger.info('[__get_adgroup_by_id] Success, adgroup_id:%s, adgroup_info:%s' %
                    (adgroup_id, adgroup_info))
                return adgroup_info
            raise Exception('Not found adgroupId!')
        except Exception as e:
            self.wflogger.exception('[__get_adgroup_by_id] Exception, adgroup_id:%s, reason:%s' % \
                (adgroup_id, e))
            return False


    '''
    获取keyword信息
    '''
    def __get_keyword_by_id(self, keyword_id):
        try:
            collection = self.db.keyword_info
            keyword_info = collection.find_one({"keywordList.keywordId":long(keyword_id)})
            if keyword_info:
                self.logger.info('[__get_keyword_by_id] Success, keyword_id:%s, keyword_info:%s' %
                    (keyword_id, keyword_info))
                return keyword_info
            raise Exception('Not found adgroupId!')
        except Exception as e:
            self.wflogger.exception('[__get_keyword_by_id] Exception, keyword_id:%s, reason:%s' % \
                (keyword_id, e))
            return False


    '''
    获取product Ads信息
    '''
    def __get_productad_by_id(self, ad_id):
        try:
            collection = self.db.productad_info
            productad_info = collection.find_one({"adId":long(ad_id)})
            if productad_info:
                self.logger.info('[__get_productad_by_id] Success, ad_id:%s, productad_info:%s' %
                    (ad_id, productad_info))
                return productad_info
            raise Exception('Not found adId!')
        except Exception as e:
            self.wflogger.exception('[__get_productad_by_id] Exception, ad_id:%s, reason:%s' % \
                (ad_id, e))
            return False


    '''
    下载报表文件
    '''
    def __download_amazon_file(self, amazon_location, save_path):
        try:
            amazon_report_path = self.amazon_api.download_amazon_file(amazon_location, save_path)
            if amazon_report_path['status']:
                self.logger.info('[__download_amazon_file] Success, amazon_location:%s, amazon_report_path:%s' % \
                    (amazon_location, amazon_report_path['file_path']))
                return amazon_report_path['file_path']
            raise Exception(amazon_report_path)
        except Exception as e:
            self.wflogger.exception('[__download_amazon_file] Exception, amazon_location:%s, reason:%s' % \
                (amazon_location, e))
            return False


    '''
    读取报表文件，构造数据 
    '''
    def __read_amazon_file(self, amazon_file):
        try:
            if not amazon_file: raise Exception('Unknow amazon_file!')

            if os.path.exists(amazon_file):
                amazon_file_path = os.path.abspath(os.path.dirname(amazon_file))
                (amazon_json_file, extension) = os.path.splitext(amazon_file)
                status, output = commands.getstatusoutput('/bin/gunzip %s' % (amazon_file))
                if status == 0: #Linux 命令0代表成功
                    with open(os.path.join(amazon_file_path, amazon_json_file)) as json_data:
                        amazon_report_data = json.load(json_data)
                        self.logger.info('[__read_amazon_file] Success, amazon_file:%s, amazon_report_data:%s' % \
                            (amazon_file, amazon_report_data))
                        return amazon_report_data
            else:
                raise Exception('File not exists!')
        except Exception as e:
            self.wflogger.exception('[__read_amazon_file] Exception, amazon_file:%s, reason:%s' % \
                (amazon_file, e))
            return []



    '''
    读取完数据后，删除下载下来的文件
    '''
    def __delete_amazon_file(self, amazon_file):
        if os.path.exists(amazon_file):
            os.remove(amazon_file)



    '''
    构建用于保存的Json数据
    '''
    def __build_report_data(self, report_info, amazon_report_data):
        report_data = {}
        try:
            report_data["reportId"]     = report_info["reportId"]
            report_data["profileId"]    = report_info["profileId"]
            report_data["reportDate"]   = int(report_info["reportDate"])
            report_data["updateTime"]   = int(time.time())

            #Amazon这里真是脑残，返回的recordType和接口中传入的都不一样，为什么返回就没有"s"了，被开发人员吃了吗？？
            if report_info['recordType'].lower() == 'campaign':
                report_data["campaignId"] = amazon_report_data["campaignId"]
                amazon_report_data.pop('campaignId')

            # campaign 统计数据
            elif report_info['recordType'].lower() == 'adgroup':
                adgroup_info = self.__get_adgroup_by_id(amazon_report_data["adGroupId"])
                if adgroup_info:
                    report_data["campaignId"] = adgroup_info["campaignId"]
                else:
                    raise Exception("Not found adgroup info, adgroup_id:%s" % str(amazon_report_data["adGroupId"]))
                report_data["adGroupId"] = amazon_report_data["adGroupId"]
                amazon_report_data.pop('adGroupId')

            # keyword 统计数据
            elif report_info['recordType'].lower() == 'keyword':
                keyword_info = self.__get_keyword_by_id(amazon_report_data["keywordId"])
                if keyword_info:
                    report_data["campaignId"]   = keyword_info["campaignId"]
                    report_data["adGroupId"]    = keyword_info["adGroupId"]
                else:
                    raise Exception("Not found keyword info, keyword_id:%s" % str(amazon_report_data["keywordId"]))
                report_data["keywordId"] = amazon_report_data["keywordId"]
                amazon_report_data.pop('keywordId')

            # product ad 统计数据
            elif report_info['recordType'].lower() == 'productad':
                productad_info = self.__get_productad_by_id(amazon_report_data["adId"])
                if productad_info:
                    report_data["campaignId"]   = productad_info["campaignId"]
                    report_data["adGroupId"]    = productad_info["adGroupId"]
                else:
                    raise Exception("Not found product info, adId:%s" % (amazon_report_data["adId"]))
                report_data["adId"] = amazon_report_data["adId"]
                amazon_report_data.pop('adId')
            #将数据扩大1000000倍，便于存储
            for attribute in amazon_report_data:
                amazon_report_data[attribute] = int(amazon_report_data[attribute]*1000000)
            report_data["reportData"] = amazon_report_data
            return report_data
        except Exception as e:
            self.wflogger.exception('[__build_report_data] Exception, report_info:%s, amazon_report_data:%s, reason:%s' %\
                (report_info, amazon_report_data, e))
            return report_data



    '''
    保存报表数据到DB
    '''
    def __save_report_data(self, report_info, report_data):
        try:
            #如果返回的为adgroup数据
            if report_info['recordType'].lower() == 'adgroup':
                collection = self.db.houyi_adgroup_report_daily
                query = {
                    "reportDate": int(report_info["reportDate"]),
                    "adGroupId": int(report_data["adGroupId"])
                }

            #返回keyword数据
            elif report_info['recordType'].lower() == 'keyword':
                collection = self.db.houyi_keyword_report_daily
                query = {
                    "reportDate": int(report_info["reportDate"]),
                    "keywordId": int(report_data["keywordId"])
                }

            #返回campaign数据
            elif report_info['recordType'].lower() == 'campaign':
                collection = self.db.houyi_campaign_report_daily
                query = {
                    "reportDate": int(report_info["reportDate"]),
                    "campaignId": int(report_data["campaignId"])
                }

            #返回product ad数据
            elif report_info['recordType'].lower() == 'productad':
                collection = self.db.houyi_productad_report_daily
                query = {
                    "reportDate": int(report_info["reportDate"]),
                    "adId": int(report_data["adId"])
                }
            #返回脑残数据
            else:
                raise Exception('Unknow record_type!')

            result = collection.update(query, report_data, True, False)
            if result:
                self.logger.info('[__save_report_data] Success, report_info:%s, report_data:%s, query:%s, result:%s' % \
                    (report_info, report_data, query, result))
                return result
            raise Exception('Report Insert Failed, result:%s' % result)
        except Exception as e:
            self.wflogger.exception('[__save_report_data] Exception, report_data:%s, reason:%s' % (report_data, e))
            return False



    '''
    线程执行方法
    '''
    def run(self):
        while True:
            try:
                queue_report_info = self.redis.lpop('report_queue')
                if queue_report_info:
                    report_info = eval(queue_report_info)
                    self.logger.info('[report_working_run] Info, report_info:%s' % report_info)
                    access_token        = report_info['accessToken']
                    report_id           = report_info["reportId"]
                    record_type         = report_info["recordType"]
                    profile_id          = report_info["profileId"]
                    report_date         = report_info["reportDate"]
                    user_id             = report_info["userId"]

                    try:
                        self.amazon_api = self.__init_amazon_api(access_token, profile_id)
                        report_exec_info = self.__get_amazon_report(report_id)
                        #如果access_token过期，则重新获取
                        if "code" in report_exec_info and report_exec_info["code"] == "401":
                            access_token = self.parent.get_access_token(user_id, profile_id)
                            self.amazon_api = self.__init_amazon_api(access_token, profile_id)
                            report_exec_info = self.__get_amazon_report(report_id)
                    except Exception as e:
                        self.wflogger.exception('[report_working_run] Exception, access_token:%s, reason:%s' % (access_token, e))
                        continue

                    #当状态为Success的时候，获取Amazon返回的location，通过location去获取数据报表
                    if "status" in report_exec_info and report_exec_info['status'] == 'SUCCESS':
                        amazon_location = report_exec_info['location']
                        amazon_file_path = '%s/%s_%s_report.json.gz' % (settings.REPORT_SERVER_DATA_PATH, record_type, report_date)
                        download_amazon_file = self.__download_amazon_file(amazon_location, amazon_file_path)
                        report_data_list = self.__read_amazon_file(download_amazon_file)
                        if report_data_list:
                            for amazon_report_data in report_data_list:
                                report_data = self.__build_report_data(report_info, amazon_report_data)
                                self.__save_report_data(report_info, report_data)
                        self.__delete_amazon_file(download_amazon_file)
                    #如果状态不为Success，则继续放回到队列中，等待下一次执行
                    else:
                        self.redis.lpush('report_queue', report_info)
                time.sleep(10)
            except Exception as e:
                self.wflogger.exception(e)
