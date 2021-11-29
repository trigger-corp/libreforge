from setuptools import setup, find_packages
import sys, os

version = '1.0'

setup(name='generate',
    version=version,
    description="",
    long_description="""\
    """,
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Nobody',
    author_email='nobody@example.com',
    url='https://example.com',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
    ],
    entry_points={
        'console_scripts': [
            'forge-generate = generate.main:main',
            'forge-inspector = internal.generate_inspector:main',
            'forge-module-test-app = internal.generate_module_test_app:main'
        ]
    }
)
