"""
Django settings for ore project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def from_env(env_name, default=None):
    value = os.environ.get(env_name, default)
    if value is None:
        raise ValueError("Environment variable '{}' must be set or have a default".format(env_name))
    return value

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '9a+sonh+etrs&3q+g5&-5=)db@^az8dy*ngjeqi()66qy4q2dz'

DEBUG = False

TEMPLATE_DEBUG = False

ALLOWED_HOSTS = []

AUTH_USER_MODEL = 'accounts.OreUser'

# Application definition

INSTALLED_APPS = (
    'grappelli',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'crispy_forms',
    'reversion',

    'rest_framework',
    'rest_framework.authentication',

    'ore.core',
    'ore.accounts',
    'ore.projects',
    'ore.teams',
    'ore.versions',
    'ore.flags'
)

MIDDLEWARE_CLASSES = (
    'reversion.middleware.RevisionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.request",
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
)

ROOT_URLCONF = 'ore.urls'

WSGI_APPLICATION = 'ore.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'

# Default location for static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Additional static directories
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)

# Static file serving with whitenoise
USE_WHITENOISE = False

# Templates
TEMPLATE_DIRS = ()

LOGIN_REDIRECT_URL = '/'

### Crispy Forms
CRISPY_TEMPLATE_PACK = 'bootstrap3'

### Prohibited names (for namespaces, and projects, and versions)
PROHIBITED_NAMES = (
    'manage',
    'new',
    'delete',
    'flag',
    'explore',
    'describe',
    'rename',
    'upload',
    'versions',
    'version',
    'projects',
    'project',
    'admin',
    'administrator',
)

# REST stuff
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (

    )
}
