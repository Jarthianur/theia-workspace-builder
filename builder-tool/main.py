#!/usr/bin/env python3

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

import click
import yaml
from pathlib import Path
import json
import jinja2
import sys
import docker
import logging
import validation


class PrepareError(Exception):
    pass


def fail(msg):
    logging.error(msg)
    sys.exit(1)


def resolvePackageJson(fpath, deps, plugs):
    if not Path(fpath).is_file():
        return
    try:
        with fpath.open('r') as pkg_json:
            pkg = json.load(pkg_json)
            if 'dependencies' in pkg:
                deps.update(pkg['dependencies'])
            if 'theiaPlugins' in pkg:
                plugs.update(pkg['theiaPlugins'])
    except Exception as e:
        logging.warning("Could not read %s. Cause: %s" % (fpath, e))


def preparePackageJson(ctx):
    pkg_tmpl = ctx.obj['TMPL_ENV'].get_template('package.json.j2')
    deps = dict()
    plugs = dict()
    app_yml = ctx.obj['APP_YAML']
    app_dir = ctx.obj['APP_DIR']

    for mod in app_yml.get('modules') or ():
        resolvePackageJson(Path(ctx.obj['MOD_DIR'], 'modules', mod, 'package.json').resolve(),
                           deps, plugs)
    resolvePackageJson(Path(app_dir, 'module', 'package.json').resolve(),
                       deps, plugs)

    fpath = Path(app_dir, 'package.json').resolve()
    try:
        with fpath.open('w') as res:
            res.write(pkg_tmpl.render(app=app_yml['app'], package={
                'dependencies': deps.items(), 'theiaPlugins': plugs.items()}))
    except Exception as e:
        raise PrepareError("Failed to write %s! Cause: %s" % (fpath, e))


def resolveDockerfile(fpath, scripts, params):
    if not Path(fpath).is_dir():
        return
    try:
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(
            fpath))
        dock = env.get_template('Dockerfile.j2')
        scripts.append(dock.render(parameters=params))
    except Exception as e:
        logging.warning("Could not read %s. Cause: %s", fpath, e)


def prepareDockerfile(ctx):
    dock_tmpl = ctx.obj['TMPL_ENV'].get_template('Dockerfile.j2')
    scripts = list()
    app_yml = ctx.obj['APP_YAML']
    app_dir = ctx.obj['APP_DIR']

    for mod in app_yml.get('modules') or ():
        resolveDockerfile(Path(ctx.obj['MOD_DIR'], 'modules', mod, app_yml['app']['base']).resolve(),
                          scripts, app_yml.get('parameters', {}).get(mod))
    resolveDockerfile(Path(app_dir, 'module').resolve(),
                      scripts, app_yml.get('parameters', {}).get(mod))

    fpath = Path(app_dir, 'Dockerfile').resolve()
    try:
        with fpath.open('w') as res:
            res.write(dock_tmpl.render(scripts=scripts))
    except Exception as e:
        raise PrepareError("Failed to write %s! Cause: %s" % (fpath, e))


def initAppDir(ctx, app_dir):
    if 'APP_DIR' in ctx.obj:
        return
    ctx.obj['APP_DIR'] = app_dir
    fpath = Path(app_dir, 'application.yaml').resolve()
    try:
        with fpath.open('r') as app_yaml:
            ctx.obj['APP_YAML'] = yaml.safe_load(app_yaml)
    except (yaml.YAMLError, FileNotFoundError) as e:
        fail("Failed to parse %s! Cause: %s" % (fpath, e))
    try:
        validation.validate(ctx.obj['APP_YAML'])
    except validation.ValidationError as e:
        fail(e)


@click.group()
@click.pass_context
def cli(ctx):
    """Build custom Eclipse Theia workspaces (applications) from language / environment modules.
    An application is defined by an 'application.yaml' file inside the APP_DIR directory.
    """
    ctx.ensure_object(dict)
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%m/%d/%Y %H:%M:%S", level=logging.INFO)


@cli.command()
@click.argument('app_dir', type=click.Path(exists=True, file_okay=False))
@click.option('-m', '--module-dir', 'mod_dir',  type=click.Path(exists=True, file_okay=False),
              help="Path to the theia-workspace-builder root. The 'modules', and 'base' directories are placed there.")
@click.pass_context
def prepare(ctx, app_dir, mod_dir):
    """Prepare the application build.
    Generates a Dockerfile and package.json inside APP_DIR.
    As 'prepare' should not run as privileged user, it needs to be invoked separately before 'build'.
    """
    initAppDir(ctx, app_dir)
    if mod_dir:
        ctx.obj['MOD_DIR'] = mod_dir
    else:
        ctx.obj['MOD_DIR'] = Path(ctx.obj['APP_DIR'], '..').resolve()

    try:
        ctx.obj['TMPL_ENV'] = jinja2.Environment(
            loader=jinja2.FileSystemLoader(
                [Path(ctx.obj['MOD_DIR'], 'base').resolve(strict=True),
                 Path(ctx.obj['MOD_DIR'], 'base', ctx.obj['APP_YAML']['app']['base']).resolve(strict=True)]
            ))
        preparePackageJson(ctx)
        prepareDockerfile(ctx)
        logging.info("Successfully prepared '%s' at [%s]. You may know build the container.",
                     ctx.obj['APP_YAML']['app']['name'], ctx.obj['APP_DIR'])
    except (jinja2.TemplateError, FileNotFoundError) as e:
        fail("Failed read template files! Cause: %s" % e)
    except (KeyError, TypeError) as e:
        fail("Failed to access required field! Cause: %s" % e)
    except PrepareError as e:
        fail(e)


@cli.command()
@click.argument('app_dir', type=click.Path(exists=True, file_okay=False))
@click.option('--latest/--no-latest', 'latest', default=True,
              help="Additionally to the version tag, add a 'latest' tag to the image.")
@click.pass_context
def build(ctx, app_dir, latest):
    """Build the application.
    Prudoces a docker image for the application specified in APP_DIR.
    Assumes 'prepare' has been invoked successfully.
    """
    initAppDir(ctx, app_dir)
    client = docker.APIClient(base_url='unix://var/run/docker.sock')
    app_yml = ctx.obj['APP_YAML']
    repo = "%s/%s" % (app_yml['app']['org'],
                      app_yml['app']['name'])

    logging.info("Building docker image for %s. This may take a while.", repo)

    img = None
    try:
        stream = client.build(
            decode=True,
            path=app_dir,
            tag=("%s:%s" % (repo, app_yml['app']['version'])),
            buildargs=app_yml.get('build', {}).get('arguments')
        )
        for chunk in stream:
            if 'stream' in chunk:
                for line in chunk['stream'].splitlines():
                    click.echo(line.rstrip())
            elif 'aux' in chunk:
                img = chunk['aux']['ID']
        if not img:
            fail("Failed to retrieve image ID from build! Something must have gone wrong.")
        logging.info("Successfully built docker image.")
    except docker.errors.APIError as e:
        fail("Failed to build the application! Cause: %s" % e)

    registry = app_yml.get('build', {}).get('registry')
    try:
        if registry:
            client.tag(img, "%s/%s" % (registry, repo), "%s" %
                       app_yml['app']['version'], force=True)
        if latest:
            client.tag(img, ("%s/%s" % (registry, repo))
                       if registry else repo, "latest", force=True)
    except docker.errors.APIError as e:
        fail("Failed to tag docker image! Cause: %s" % e)


if __name__ == '__main__':
    cli(obj={})
