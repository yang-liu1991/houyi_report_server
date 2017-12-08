#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
Author: liuyang@xxx.cn
Created Time: 2017-10-19 16:05:17
"""

import json
import time
import logging
import requests
import commands

from django_settings import AMAZON_ADVERTISING_API, CLIENT_ID, CLIENT_SECRET

class AmazonAdvertisingApi(object):
    def __init__(self, access_token, scope):
        self.access_token	= access_token
        self.scope			= scope
        self.response_type	= 'code'
        self.api_version	= 'v1'
        self.date			= time.strftime('%Y%m%d', time.localtime(time.time()))
        self.logger		= logging.getLogger('amazon_advertising_api_info')
        self.wflogger	= logging.getLogger('amazon_advertising_api_wf')


    '''
    定义调用API Headers
    '''
    def __get_api_headers(self):
        headers = {
            'content-type':'application/json',
            'authorization':self.access_token,
            'Amazon-Advertising-API-Scope':self.scope
        }
        return headers


    '''
    获取Profiles
    '''
    def get_user_profiles(self):
        headers = self.__get_api_headers()
        try:
            url = '%s/%s/profiles' % (AMAZON_ADVERTISING_API, self.api_version)
            response = requests.get(url, headers=headers)
            self.logger.info('[get_user_profiles] Info, access_token:%s, response:%s' % \
                (self.access_token, response.json()))
            return response.json()
        except Exception as e:
            self.wflogger.exception('[get_user_profiles] Exception, access_token:%s, reason:%s' % (self.access_token, e))
            return {'status':False, 'error_message':e}


    '''
    提交生成报表任务
    '''
    def set_amazon_report(self, report_date, report_type):
        data_dict = {
            'campaignType':'sponsoredProducts',
            #'segment':'query',
            'reportDate':report_date,
            'metrics':'clicks,impressions,cost,attributedConversions1dSameSKU,attributedConversions1d,attributedSales1dSameSKU,attributedSales1d,attributedConversions7dSameSKU,attributedConversions7d,attributedSales7dSameSKU,attributedSales7d,attributedConversions30dSameSKU,attributedConversions30d,attributedSales30dSameSKU,attributedSales30d'
        }
        headers = self.__get_api_headers()
        try:
            url = '%s/%s/%s/report' % (AMAZON_ADVERTISING_API, self.api_version, report_type)
            response = requests.post(url, data=json.dumps(data_dict), headers=headers)
            self.logger.info('[set_amazon_report] Info, report_type:%s, report_date:%s, response:%s' % \
                (report_type, report_date, response.json()))
            return response.json()
        except Exception as e:
            self.wflogger.exception('[set_amazon_report] Exception, report_type:%s, report_date:%s, reason:%s' % \
                (report_type, report_date, e))
            return {'status':False, 'error_message':e}


    '''
    获取报表任务信息
    '''
    def get_amazon_report(self, report_id):
        headers = self.__get_api_headers()
        try:
            url = '%s/%s/reports/%s' % (AMAZON_ADVERTISING_API, self.api_version, report_id)
            response = requests.get(url, headers=headers)
            self.logger.info('[get_amazon_report] Info, report_id:%s, response:%s' % (report_id, response.json()))
            return response.json()
        except Exception as e:
            self.wflogger.exception('[get_amazon_report] Exception, report_id:%s, reason:%s' % (report_id, e))
            return {'status':False, 'error_message':e}


    '''
    下载文件
    '''
    def download_amazon_file(self, aws_url, amazon_file_path):
        headers = self.__get_api_headers()
        try:
            session = requests.Session()
            response = session.get(aws_url, headers=headers)
            s3_server_location = response.url
            status, output = commands.getstatusoutput('curl -o %s "%s"' % (amazon_file_path, s3_server_location))
            if status == 0:
                self.logger.info('[download_amazon_file] Success, aws_url:%s, date:%s, amazon_file_path:%s' % \
                    (aws_url, self.date, amazon_file_path))
                return {'status':True, 'file_path':amazon_file_path}
            raise Exception(output)
        except Exception as e:
            self.wflogger.exception('[download_amazon_file] Exception, aws_url:%s, reason:%s' % (aws_url, e))
            return {'status':False, 'error_message':e}


    '''
    提交快照任务
    '''
    def set_amazon_snapshots(self, record_type, state_filter=''):
        headers = self.__get_api_headers()
        data_dict = {'campaignType':'sponsoredProducts'}
        if state_filter: data_dict['stateFilter'] = state_filter
        try:
            url = '%s/%s/%s/snapshot' % (AMAZON_ADVERTISING_API, self.api_version, record_type)
            response = requests.post(url, data=json.dumps(data_dict), headers=headers)
            self.logger.info('[set_amazon_snapshots] Info, record_type:%s, state_filter:%s, response:%s' % \
                (record_type, state_filter, response.json()))
            return response.json()
        except Exception as e:
            self.wflogger.exception('[set_amazon_snapshots] Exception, record_type%s, state_filter:%s, reason:%s' % \
                (record_type, state_filter, e))
            return {'status':False, 'error_message':e}


    '''
    获取快照任务
    '''
    def get_amazon_snapshots(self, snapshot_id):
        headers = self.__get_api_headers()
        try:
            url = '%s/%s/snapshots/%s' % (AMAZON_ADVERTISING_API, self.api_version, snapshot_id)
            response = requests.get(url, headers=headers)
            self.logger.info('[get_amazon_snapshots] Info, snapshot_id:%s, response:%s' % \
                (snapshot_id, response.json()))
            return response.json()
        except Exception as e:
            self.wflogger.exception('[get_amazon_snapshots] Exception, snapshot_id:%s, reason:%s' % \
                (snapshot_id, e))
            return {'status':False, 'error_message':e}



    '''
    获取campaigns数据
    '''
    def get_amazon_campaigns(self, **params):
        headers = self.__get_api_headers()
        try:
            url = '%s/%s/campaigns/extended' % (AMAZON_ADVERTISING_API, self.api_version)
            if params:
                response = requests.get(url, params=params, headers=headers)
                self.logger.info('[get_amazon_campaigns], params:%s, response:%s' % \
                    (params, response.json()))
            else:
                response = requests.get(url, headers=headers)
                self.logger.info('[get_amazon_campaigns], response:%s' % (response.json()))
            return response.json()
        except Exception as e:
            self.wflogger.exception('[get_amazon_campaigns] Exception, reason:%s' % (e))
            return {'status': False, 'error_message': e}


    '''
    获取ad groups数据
    '''
    def get_amazon_adgroups(self, **params):
        headers = self.__get_api_headers()
        try:
            url = '%s/%s/adGroups/extended' % (AMAZON_ADVERTISING_API, self.api_version)
            if params:
                response = requests.get(url, params=params, headers=headers)
                self.logger.info('[get_amazon_adgroups], params:%s, response:%s' % (params, response.json()))
            else:
                response = requests.get(url, headers=headers)
                self.logger.info('[get_amazon_adgroups], response:%s' % (response.json()))
            return response.json()
        except Exception as e:
            self.wflogger.exception('[get_amazon_adgroups] Exception, reason:%s' % (e))
            return {'status': False, 'error_message': e}



    '''
    获取product ads数据
    '''
    def get_amazon_productads(self, **params):
        headers = self.__get_api_headers()
        try:
            url = '%s/%s/productAds/extended' % (AMAZON_ADVERTISING_API, self.api_version)
            if params:
                response = requests.get(url, params=params, headers=headers)
                self.logger.info('[get_amazon_productads], params:%s, response:%s' % (params, response.json()))
            else:
                response = requests.get(url, headers=headers)
                self.logger.info('[get_amazon_productads], response:%s' % (response.json()))
            return response.json()
        except Exception as e:
            self.wflogger.exception('[get_amazon_productads] Exception, reason:%s' % (e))
            return {'status': False, 'error_message': e}


    '''
    获取keywords数据
    '''
    def get_amazon_keywords(self, params={}):
        headers = self.__get_api_headers()
        try:
            url = '%s/%s/keywords/extended' % (AMAZON_ADVERTISING_API, self.api_version)
            if params:
                response = requests.get(url, params=params, headers=headers)
                self.logger.info('[get_amazon_keywords], params:%s, response:%s' % (params, response.json()))
            else:
                response = requests.get(url, headers=headers)
                self.logger.info('[get_amazon_keywords], response:%s' % (response.json()))
            return response.json()
        except Exception as e:
            self.wflogger.exception('[get_amazon_keywords] Exception, reason:%s' % (e))
            return {'status': False, 'error_message': e}





# vim: set noexpandtab ts=4 sts=4 sw=4 :
