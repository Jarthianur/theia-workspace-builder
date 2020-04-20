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

from schema import Schema, SchemaError, Optional, Regex, And, Or


class ValidationError(Exception):
    pass


APPLICATION_YAML = {
    'app': {
        'name': And(str, len),
        'version': And(str, len),
        'org': And(str, len),
        'license': And(str, len),
        'title': And(str, len),
        'base': And(str, len)
    },
    Optional('parameters'): {
        Optional(str): Or(dict, None)
    },
    Optional('build'): {
        Optional('registry'): Or(And(str, len), None),
        Optional('arguments'): Or(dict, None)
    },
    Optional('modules'): Or([
        And(str, len),
    ], None)
}


def validate(yaml):
    try:
        return Schema(APPLICATION_YAML).validate(yaml)
    except SchemaError as e:
        raise ValidationError("Invalid application.yaml! Cause: %s" % e)
