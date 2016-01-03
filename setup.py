# -*- coding: utf-8 -*-

from setuptools import (
    find_packages,
    setup,
)


requires = [
    'pyramid',
    'pyramid_tm',
    'pyramid_jinja2',
    'SQLAlchemy',
    'transaction',
    'zope.sqlalchemy',
]

setup(name='photos',
      version='0.1',
      description='photos.yosida95.com',
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pyramid",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      author='Kohei YOSHIDA',
      author_email='kohei@yosida95.com',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='photos',
      install_requires=requires,
      entry_points={
          'paste.app_factory': [
              'main = photos:main',
          ],
          'console_scripts': [
              'initialize_photos_db = photos.scripts.initializedb:main',
          ]
      })
