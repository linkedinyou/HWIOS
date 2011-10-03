# -*- coding: utf-8 -*-
"""
    settings
    ~~~~~~~~

    General django settings file for HWIOS

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

import os,sys
from ConfigParser import ConfigParser
ugettext = lambda s: s
DEFAULT_CHARSET = 'utf-8'
SERVICE_ROOT = os.path.dirname(os.path.realpath(__file__))
#Fix for config options in hwios main executable, which call django specific stuff from service subdirs
if 'HWIOS_ROOT' in os.environ:
    HWIOS_ROOT = os.environ['HWIOS_ROOT']
else:
    HWIOS_ROOT = os.getcwd()
    if 'services/web_ui' in HWIOS_ROOT:
        HWIOS_ROOT = HWIOS_ROOT[:-15]
    os.putenv('HWIOS_ROOT', HWIOS_ROOT)
sys.path.append(os.path.join(HWIOS_ROOT,'../'))
service_config = ConfigParser()
service_config.read(os.path.join(SERVICE_ROOT,'service.ini'))
hwios_config = ConfigParser()
hwios_config.read(os.path.join(HWIOS_ROOT,'hwios.ini'))

HWIOS_URI = hwios_config.get('general','uri')
HWIOS_PORT = service_config.get('service','port')

DEBUG = hwios_config.getboolean('general','debug')
TEMPLATE_DEBUG = DEBUG
ADMINS = (('admin', 'admin@mycollabsite.org'))
MANAGERS = ADMINS
USE_I18N = True

SECRET_KEY = service_config.get('general','secret_key')
TIME_ZONE = service_config.get('general', 'time_zone')
#LANGUAGE_CODE = service_config.get('general','lang')
ADMIN_MEDIA_PREFIX = 'admin'
ROOT_URLCONF = 'web_ui.urls'
SITE_ID = 1
#CACHE_BACKEND = service_config.get('general','cache')
if service_config.get('general','session') == 'db':
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
elif service_config.get('general','session') == 'cache':
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
DATABASE_ROUTERS = ['web_ui.models.router.HWIOSRouter']
DATABASES = {
    'default': {
        'NAME': hwios_config.get('db', 'name'),
        'ENGINE': 'django.db.backends.mysql',
        'USER': hwios_config.get('db', 'user'),
        'PASSWORD': hwios_config.get('db', 'pw'),
        'PORT': hwios_config.get('db', 'port'),
        'HOST': hwios_config.get('db', 'host')
    },
    'grid': {
        'NAME': hwios_config.get('db', 'grid'),
        'ENGINE': 'django.db.backends.mysql',
        'USER': hwios_config.get('db', 'user'),
        'PASSWORD': hwios_config.get('db', 'pw'),
        'PORT': hwios_config.get('db', 'port'),
        'HOST': hwios_config.get('db', 'host')
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = hwios_config.get('email', 'host')
EMAIL_HOST_USER = hwios_config.get('email', 'user')
EMAIL_HOST_PASSWORD = hwios_config.get('email', 'pw')
EMAIL_PORT = hwios_config.get('email', 'port')
EMAIL_USE_TLS = hwios_config.getboolean('email', 'tls')

LANGUAGES = (
  ('nl', ugettext('Dutch')),
  ('en', ugettext('English')),
)

AUTHENTICATION_CONFIG = 'default'
AUTHENTICATION_BACKENDS = ('web_ui.auth.%s.XAuth' % AUTHENTICATION_CONFIG,)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",)

TEMPLATE_DIRS = (
    os.path.join(SERVICE_ROOT, 'templates/%s/' % (service_config.get('general', 'template'))), 
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',    
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'web_ui.models.dj_tracker.TrackerMiddleware',
    )

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sitemaps',
    'django.contrib.sessions',
    'django.contrib.sites',
    'web_ui',
    'web_ui.models',
    'web_ui.models.no_fixture',
    )

SERVICE_TYPES = (
    (0, 'StandAlone Vanilla'),
    (1, 'StandAlone ModRex'),
    (2, 'Grid Service'),
    (3, 'ModRex Service'),
    (4, 'Vanilla Simulator'),
    (5, 'ModRex Simulator'),
    (6, 'Web Service'),
)