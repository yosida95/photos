# -*- coding: utf-8 -*-

from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from photos.models import (
    Base,
    DBSession,
)


def bootstrap(settings):
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine


def main(global_config, **settings):
    bootstrap(settings)

    config = Configurator(settings=settings)
    config.scan()
    return config.make_wsgi_app()
