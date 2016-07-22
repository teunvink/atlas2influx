from codecs import open as codecs_open
from setuptools import setup, find_packages


# Get the long description from the relevant file
with codecs_open('README.rst', encoding='utf-8') as f:
    long_description = f.read()


setup(name='atlas2influx',
      version='0.1',
      description='RIPE Atlas to InfluxDB',
      long_description=long_description,
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6'
      ],
      keywords='ripe atlas influxDB',
      author='Tobias Rueetschi',
      author_email='tr@brief.li',
      url='https://github.com/2-B/atlas2influx.git',
      license='GPLv3',
      packages=find_packages(),
      install_requires=[
          'PyYAML',
          'ripe.atlas.cousteau',
      ],
      extras_require={
          'test': ['pytest'],
      },
      entry_points="""
      [console_scripts]
      atlas2influx=atlas2influx.main:main
      """
      )
