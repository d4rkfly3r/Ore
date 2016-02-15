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


def from_env(env_options, default=None):
    value = None
    if isinstance(env_options, str):
        value = os.environ.get(env_options, None)
    else:
        for option in env_options:
            if option in os.environ:
                value = os.environ[option]
                break
    if value is None:
        if default is not None:
            return default
        else:
            raise ValueError(
                "Environment variable(s) '{}' must be set or have a default".format(env_options))
    return value

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '9a+sonh+etrs&3q+g5&-5=)db@^az8dy*ngjeqi()66qy4q2dz'

DEBUG = False

ALLOWED_HOSTS = []

AUTH_USER_MODEL = 'accounts.OreUser'

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'compressor',

    'crispy_forms',
    'reversion',
    'actstream',

    'rest_framework',

    'ore.core',
    'ore.accounts',
    'ore.organizations',
    'ore.projects',
    'ore.teams',
    'ore.versions',
    'ore.flags',
    'ore.discourse_sso',
    'ore.discourse_discuss',
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

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',

    # compressor finder
    'compressor.finders.CompressorFinder',
)

# Default location for static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Compression
COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.core.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.core.context_processors.debug",
                "django.core.context_processors.i18n",
                "django.core.context_processors.media",
                "django.core.context_processors.static",
                "django.core.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "ore.core.context_processors.build_stamp",
            ]
        }
    },
]

LOGIN_REDIRECT_URL = '/'

# Activity Stream

ACTSTREAM_SETTINGS = {
    'MANAGER': 'actstream.managers.ActionManager',
    'FETCH_RELATIONS': True,
    'USE_JSONFIELD': False,
}

# Crispy Forms
CRISPY_TEMPLATE_PACK = 'bootstrap3'

# Django Sites Framework
SITE_ID = 1

# Prohibited names (for namespaces, and projects, and versions)
PROHIBITED_NAMES = (
    'manage',
    'new',
    'create',
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
    'static',
    'settings',
    'config',
    'setting',
    'login',
    'logout',
    'log-in',
    'log-out',
    'user',
    'users',
    'accounts',
    'account',
    'organization',
    'organizations',
    'org',
    'orgs',
    'staff',
    'sponge',
    'spongepowered',
    'spongeproject',
    'platform',
    'admins',
    'ore',
)

BUILD_STAMP_PATH = os.path.join(os.path.dirname(BASE_DIR), 'build_stamp.txt')

BUILD_STAMP = None
if os.path.exists(BUILD_STAMP_PATH):
    with open(BUILD_STAMP_PATH, 'r') as f:
        BUILD_STAMP = f.read().strip()

DISCOURSE_SSO_ENABLED = from_env('DISCOURSE_SSO_ENABLED', False) == 'true'
if DISCOURSE_SSO_ENABLED:
    DISCOURSE_SSO_URL = from_env(
        'DISCOURSE_SSO_URL', 'https://forums.spongepowered.org/session/sso_provider')
    DISCOURSE_SSO_SECRET = from_env('DISCOURSE_SSO_SECRET')

DISCOURSE_DISCUSS_ENABLED = from_env(
    'DISCOURSE_DISCUSS_ENABLED', False) == 'true'
if DISCOURSE_DISCUSS_ENABLED:
    DISCOURSE_DISCUSS_API = from_env(
        'DISCOURSE_DISCUSS_API', 'https://forums.spongepowered.org')
    DISCOURSE_DISCUSS_CATEGORY = from_env(
        'DISCOURSE_DISCUSS_CATEGORY', 'ore')
    DISCOURSE_DISCUSS_API_KEY = from_env('DISCOURSE_DISCUSS_API_KEY')
    DISCOURSE_DISCUSS_ORE_SITE_BASE = from_env(
        'DISCOURSE_DISCUSS_ORE_SITE_BASE', 'https://ore-staging.spongepowered.org')
