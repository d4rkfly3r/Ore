import os.path
import dukpy
from django.conf import settings

basepath = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_dukpy_ctx():
    result = os.path.join(basepath, 'node_modules')
    if not os.path.exists(result):
        raise ValueError("Unable to locate node_modules directory - is Ore installed correctly?")

    ctx = dukpy.RequirableContext([result])

    def resolve_wrap(resolve):
        def inner(req_ctx, id_, search_paths):
            # bodge to work around the fact
            # that the browser version of util
            # imports inherits, which expects util to provide inherits
            # yaey
            if id_ == '!inherits!':
                id_ = '!inherits/inherits_browser.js!'

            return resolve(req_ctx, id_, search_paths)
        return inner

    ctx.finder.resolve = resolve_wrap(ctx.finder.resolve)

    return ctx


def load_mdit(ctx):
    with open(os.path.join(basepath, 'ore/core/static/ore/js/markdown.js'), 'r') as f:
        return ctx.evaljs(f.read())

ctx = load_dukpy_ctx()
mdit = None
if not settings.DEBUG:
    import logging
    logging.info("Loading markdown context")
    mdit = load_mdit(ctx)


def compile(text, context={}):
    global mdit
    if mdit is None:
        mdit = load_mdit(ctx)

    return mdit(text)
