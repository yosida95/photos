# -*- coding: utf-8 -*-

from setuptools import (
    find_packages,
    setup,
)


requires = [
    'pyramid>=1.6,<1.7',
    'pyramid_tm',
    'SQLAlchemy>=1.0,<1.1',
    'transaction',
    'zope.sqlalchemy',

    'boto>=2.38,<2.39',
    'Pillow>=3.0,<3.1',
    'PyMySQL>=0.6,<0.7',
    'pyramid_jinja2>=2.5,<2.6',
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
