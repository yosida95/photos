# -*- coding: utf-8 -*-

import json
import urllib.request
from urllib.parse import urlparse

from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPMovedPermanently,
    HTTPNotFound,
    HTTPUnauthorized,
)
from pyramid.response import Response
from pyramid.view import view_config
from sqlalchemy.sql import func

from photos.models import (
    DBSession,
    Photo,
)


def twitter_verify_credentials(request):
    provider_url = request.headers.get('X-Auth-Service-Provider')
    if not provider_url or urlparse(provider_url).netloc != 'api.twitter.com':
        return None

    verify_request = urllib.request.Request(provider_url)
    verify_request.add_header(
        'Authorization',
        request.headers.get('X-Verify-Credentials-Authorization'))
    try:
        with urllib.request.urlopen(verify_request) as resp:
            if resp.getcode() != 200:
                return None

            result = json.loads(resp.read().decode('utf8'))
            if 'error' in result:
                return None
            return result
    except:
        return None


def photo_factory(request):
    photo_id = request.matchdict['id']
    photo = DBSession.query(
        Photo
    ).filter(
        Photo.id == photo_id
    ).first()
    if photo is None:
        raise HTTPNotFound()

    return photo


@view_config(route_name='photo_list',
             request_method='GET',
             renderer='photo_list.jinja2')
def photo_list(request):
    page_str = request.GET.get('page', '')
    page = page_str.isdigit() and int(page_str) or 1

    num_photos = DBSession.query(
        func.count(Photo.id)
    ).filter(
        Photo.published == True  # noqa
    ).first()[0]
    last_page = (num_photos + 8) // 9
    if page > last_page:
        raise HTTPNotFound()

    photos = DBSession.query(
        Photo
    ).filter(
        Photo.published == True  # noqa
    ).order_by(
        Photo.created_at.desc()
    ).limit(
        9
    ).offset(
        (page - 1) * 9
    ).all()
    photos = [photos[x:x+3] for x in range(0, len(photos), 3)]
    return dict(photos=photos,
                current_page=page,
                last_page=last_page)


@view_config(route_name='photo_list_slash', request_method='GET')
def photo_list_slash(request):
    raise HTTPMovedPermanently(request.route_url('photo_list'))


@view_config(route_name='photo_detail',
             request_method='GET',
             renderer='photo_detail.jinja2')
def photo_detail(photo, request):
    return dict(photo=photo)


@view_config(route_name='photo_image', request_method='GET')
def photo_image(photo, request):
    size = request.matchdict['size']
    if size not in ('raw', 'resized', 'thumbnail'):
        raise HTTPNotFound()

    try:
        if size == 'raw':
            data = photo.get_original(request.registry.photo_storage)
        elif size == 'resized':
            resize_to = (480, 360)
            data = photo.get_resized(request.registry.photo_storage, resize_to)
        else:  # thumbnail
            data = photo.get_thumb(request.registry.photo_storage, 220)
    except KeyError as why:
        raise HTTPNotFound() from why

    return Response(data, content_type=photo.mime_type)


@view_config(route_name='upload',
             request_method='POST',
             renderer='upload.xml.jinja2')
def upload(request):
    user = request.twitter_user
    if user is None:
        raise HTTPUnauthorized()
    if user.get('id') != request.registry.uploader_twitter_id:
        raise HTTPForbidden()

    media = request.POST.get('media')
    photo = Photo(media.type, request.POST.get('message', ''))
    photo.set_content(request.registry.photo_storage, media.file.read())
    DBSession.add(photo)

    return dict(photo=photo,
                user_id=user['id'],
                user_screen_name=user.get('screen_name', ''))
