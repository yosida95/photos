# -*- coding: utf-8 -*-

from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from photos.models import (
    Base,
    DBSession,
    GehirnKVS,
)
from photos.views import (
    photo_factory,
    twitter_verify_credentials,
)


def bootstrap(settings):
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine


def main(global_config, **settings):
    bootstrap(settings)

    config = Configurator(settings=settings)

    config.registry.uploader_twitter_id = int(settings['twitter_id'])
    config.registry.photo_storage = GehirnKVS(
        settings['gehirn_kvs.access_key_id'],
        settings['gehirn_kvs.secret_access_key'],
        settings['gehirn_kvs.bucket_name'])
    config.add_request_method(callable=twitter_verify_credentials,
                              name='twitter_user',
                              property=True,
                              reify=True)

    config.add_route('photo_list', '/photos')
    config.add_route('photo_list_slash', '/photos/')
    config.add_route('upload', '/photos/upload.xml')
    config.add_route('photo_image', '/photos/{id}.{size}.{ext}',
                     factory=photo_factory)
    config.add_route('photo_detail', '/photos/{id}', factory=photo_factory)
    config.scan()

    return config.make_wsgi_app()
