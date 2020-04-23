from setuptools import setup

"""
    Copyright 2020 Jarthianur

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

setup(
    name='theia_builder',
    version='0.1',
    py_modules=['theia_builder'],
    install_requires=[
        'Click',
        'pyyaml',
        'Jinja2',
        'pathlib',
        'docker',
        'schema'
    ],
    entry_points='''
        [console_scripts]
        theia_builder=main:cli
    ''',
)