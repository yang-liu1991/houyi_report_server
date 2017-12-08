"""
Django settings for houyi_report_server project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'cx%e667@x)i1)tx(40*n^2@ps6v0r@k!a_7ca_l#1#yuiq4435'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

#amazon
AMAZON_ADVERTISING_API = 'https://advertising-api.amazon.com'
#AMAZON_ADVERTISING_API = 'https://advertising-api-test.amazon.com'
CLIENT_ID		= 'amzn1.application-oa2-client.a57f65a042c742e796ec9e855d5875b3'
CLIENT_SECRET	= '417abba8b925ef27c50d1d8ad7bdd9ad6159dedff7c1d404b1f5a192e3428950'

REPORT_SERVER_DATA_PATH = '/home/liuyang/wwwroot/houyi/houyi_report_server/data'

#redis
REDIS_HOST = '10.0.0.207'
REDIS_PORT = 16381
REDIS_DB = 10

#Mongo db
M_HOST  = '10.0.0.207'
M_USER  = ''
M_PASS  = ''
M_PORT  = 27017
M_NAME  = 'houyi'

#Info server
INFO_HOST = '10.0.0.207'
INFO_PORT = 8373
INFO_SIZE = 5

#report interval
REPORT_INTERVAL = 1800

#syncing interval
SYNCING_INTERVAL = 300


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'houyi_report_server.urls'

WSGI_APPLICATION = 'houyi_report_server.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'xxx_pyutils': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'amazon_advertising_api_info':{
            'formatter': 'default',
            'class':'logging.handlers.TimedRotatingFileHandler',
            'when':'D',
            'interval':1,
            'backupCount':30,
            'filename':  'logs/amazon_advertising_api_info.log',
        },
        'amazon_advertising_api_wf': {
            'formatter': 'default',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when':'D',
            'interval':1,
            'backupCount':30,
            'filename': 'logs/amazon_advertising_api_wf.log',
        },
        'report_info':{
            'formatter': 'default',
            'class':'logging.handlers.TimedRotatingFileHandler',
            'when':'D',
            'interval':1,
            'backupCount':30,
            'filename':  'logs/report_info.log',
        },
        'report_wf': {
            'formatter': 'default',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when':'D',
            'interval':1,
            'backupCount':30,
            'filename': 'logs/report_wf.log',
        },
        'syncing_info':{
            'formatter': 'default',
            'class':'logging.handlers.TimedRotatingFileHandler',
            'when':'D',
            'interval':1,
            'backupCount':30,
            'filename':  'logs/syncing_info.log',
        },
        'syncing_wf': {
            'formatter': 'default',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when':'D',
            'interval':1,
            'backupCount':30,
            'filename': 'logs/syncing_wf.log',
        },
    },
    'loggers': {
        'amazon_advertising_api_info':{
            'handlers':['amazon_advertising_api_info'],
            'level':'DEBUG',
            'propagate':False,
        },
        'amazon_advertising_api_wf':{
            'handlers': ['amazon_advertising_api_wf'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'report_server_info':{
            'handlers':['report_info'],
            'level':'DEBUG',
            'propagate':False,
        },
        'report_server_wf':{
            'handlers': ['report_wf'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'syncing_server_info': {
            'handlers': ['syncing_info'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'syncing_server_wf':{
            'handlers': ['syncing_wf'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'xxx_pyutils': {
            'handlers': ['xxx_pyutils'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    'formatters': {
        'default':{
            'format': '%(asctime)s %(levelname)-2s %(name)s.%(funcName)s:%(lineno)-5d %(message)s'
        }
    }
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
