# -*- coding: utf-8 -*-

import random
import string
from datetime import datetime
from io import BytesIO

from boto.exception import S3ResponseError
from boto.s3.connection import S3Connection
from PIL import Image
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
)
from sqlalchemy.schema import Column
from sqlalchemy.sql import func
from sqlalchemy.types import (
    Boolean,
    DateTime,
    Unicode,
)
from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


def _crop_photo_square(orig):
    if orig.size[0] == orig.size[1]:
        return orig

    if orig.size[0] > orig.size[1]:
        excess = orig.size[0] - orig.size[1]
        half_excess = excess // 2
        box = (half_excess,
               0,
               orig.size[0] - excess + half_excess,
               orig.size[1])
    else:
        excess = orig.size[1] - orig.size[0]
        half_excess = excess // 2
        box = (0,
               half_excess,
               orig.size[0],
               orig.size[1] - excess + half_excess)

    crop = orig.crop(box)
    crop.format = orig.format
    return crop


class Photo(Base):
    __tablename__ = 'photos'

    id = Column(Unicode(5), primary_key=True)
    mime_type = Column(Unicode(10), nullable=False, unique=False)
    comment = Column(Unicode(140), nullable=False, unique=False)
    created_at = Column(DateTime(), nullable=False, unique=False)
    thumbnail = Column(Boolean(), nullable=False, unique=False)
    resized = Column(Boolean(), nullable=False, unique=False)
    published = Column(Boolean(), nullable=False, unique=False)

    def __init__(self, mime_type, comment='', created_at=None, published=True):
        self.id = self._generate_id()
        self.mime_type = mime_type.lower()
        self.comment = comment
        self.created_at = created_at or datetime.utcnow()
        self.thumbnail = False
        self.resized = False
        self.published = published

    @property
    def ext(self):
        if not self.mime_type.startswith('image/'):
            return 'ext'
        return self.mime_type.replace('image/', '')

    @property
    def key(self):
        return '.'.join((self.id, self.ext))

    def _upload_content(self, storage, key, content):
        return storage.save(self, key, content)

    def _download_content(self, storage, key):
        return storage.get(self, key)

    def set_content(self, storage, content):
        return self._upload_content(storage, self.key, content)

    def get_original(self, storage):
        return self._download_content(storage, self.key)

    def get_thumb(self, storage, size):
        key = '{id}.thumbnail.{ext}'.format(id=self.id, ext=self.ext)
        if self.thumbnail:
            return self._download_content(storage, key)

        photo = Image.open(BytesIO(self.get_original(storage)))
        photo = _crop_photo_square(photo)
        photo.thumbnail((size, size), Image.ANTIALIAS)
        thumb = BytesIO()
        photo.save(thumb, photo.format)
        data = thumb.getvalue()

        self._upload_content(storage, key, data)
        self.thumbnail = True
        return data

    def get_resized(self, storage, size):
        key = '{id}.resized.{ext}'.format(id=self.id, ext=self.ext)
        if self.resized:
            return self._download_content(storage, key)

        photo = Image.open(BytesIO(self.get_original(storage)))
        if size[0] < size[1]:
            size = (size[1], size[0])
        if photo.size[0] < photo.size[1]:
            size = (size[1], size[0])
        photo.thumbnail(size, Image.ANTIALIAS)
        resized = BytesIO()
        photo.save(resized, photo.format)
        data = resized.getvalue()

        self._upload_content(storage, key, data)
        self.resized = True
        return data

    @classmethod
    def _is_unique_id(cls, id):
        count = DBSession.query(
            func.count(cls.id)
        ).filter(
            cls.id == id
        ).first()[0]
        return count == 0

    @classmethod
    def _generate_id(cls):
        while True:
            id = ''.join(random.choice(string.ascii_letters + string.digits)
                         for _ in range(5))
            if cls._is_unique_id(id):
                return id


class GehirnKVS:

    def __init__(self, access_key_id, secret_access_key, bucket_name,
                 hostname='kvs.gehirn.jp', is_secure=True):
        self.conn = S3Connection(host=hostname,
                                 is_secure=is_secure,
                                 aws_access_key_id=access_key_id,
                                 aws_secret_access_key=secret_access_key)
        self.bucket_name = bucket_name
        self._bucket = None

    @property
    def bucket(self):
        if not self._bucket:
            try:
                self._bucket = self.conn.get_bucket(self.bucket_name)
            except S3ResponseError:
                self._bucket = self.conn.create_bucket(self.bucket_name)

        return self._bucket

    def save(self, meta, key, value):
        obj = self.bucket.new_key(key)
        obj.set_metadata('Content-Type', meta.mime_type)
        obj.set_contents_from_string(value)
        return True

    def get(self, meta, key):
        obj = self.bucket.get_key(key)
        if obj is None:
            raise KeyError()
        return obj.get_contents_as_string()
