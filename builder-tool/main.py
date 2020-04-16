#!/usr/bin/env python

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


class PrepareError(Exception):
    pass


def fail(msg):
    click.echo(msg)
    sys.exit(1)


def resolvePackageJson(fpath, deps, plugs):
    if not Path(fpath).is_file():
        return
    try:
        with fpath.open('r') as pkg_json:
            pkg = json.load(pkg_json)
            pkg_deps = pkg.get('dependencies')
            if pkg_deps:
                deps.update(pkg_deps)
            pkg_plugs = pkg.get('theiaPlugins')
            if pkg_plugs:
                plugs.update(pkg_plugs)
    except Exception as e:
        click.echo("[WARNING] Could not read %s. Cause: %s" % (fpath, e))


def preparePackageJson(ctx):
    pkg_tmpl = ctx.obj['TMPL_ENV'].get_template('package.json.j2')
    deps = dict()
    plugs = dict()
    app_yml = ctx.obj['APP_YAML']
    app_dir = ctx.obj['APP_DIR']

    for mod in app_yml['modules']:
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
        raise PrepareError(
            "[ERROR] Failed to write %s! Cause: %s" % (fpath, e))


def resolveDockerfile(fpath, scripts):
    if not Path(fpath).is_file():
        return
    try:
        with fpath.open('r') as dockfile:
            scripts.append(dockfile.read().strip())
    except Exception as e:
        click.echo("[WARNING] Could not read %s. Cause: %s" % (fpath, e))


def prepareDockerfile(ctx):
    dock_tmpl = ctx.obj['TMPL_ENV'].get_template('Dockerfile.j2')
    scripts = list()
    app_yml = ctx.obj['APP_YAML']
    app_dir = ctx.obj['APP_DIR']

    for mod in app_yml['modules']:
        resolveDockerfile(Path(ctx.obj['MOD_DIR'], 'modules', mod, app_yml['app']['base'], 'Dockerfile').resolve(),
                          scripts)
    resolveDockerfile(Path(app_dir, 'module', 'Dockerfile').resolve(),
                      scripts)

    fpath = Path(app_dir, 'Dockerfile').resolve()
    try:
        with fpath.open('w') as res:
            res.write(dock_tmpl.render(scripts=scripts))
    except Exception as e:
        raise PrepareError(
            "[ERROR] Failed to write %s! Cause: %s" % (fpath, e))


def prepareApp(ctx):
    preparePackageJson(ctx)
    prepareDockerfile(ctx)


def initAppDir(ctx, app_dir):
    if ctx.obj.get('APP_DIR'):
        return
    ctx.obj['APP_DIR'] = app_dir
    fpath = Path(app_dir, 'application.yaml').resolve()
    try:
        with fpath.open('r') as app_yaml:
            ctx.obj['APP_YAML'] = yaml.safe_load(app_yaml)
    except (yaml.YAMLError, FileNotFoundError) as e:
        fail("[ERROR] Failed to parse %s! Cause: %s" % (fpath, e))


@click.group()
@click.pass_context
def cli(ctx):
    """Build custom Eclipse Theia workspaces (applications) from language / environment modules.
    An application is defined by an 'application.yaml' file inside the APP_DIR directory.
    """
    ctx.ensure_object(dict)


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
        prepareApp(ctx)
        click.echo("Successfully prepared '%s' at [%s]. You may know build the container."
                   % (ctx.obj['APP_YAML']['app']['name'], ctx.obj['APP_DIR']))
    except (jinja2.TemplateError, FileNotFoundError) as e:
        fail("[ERROR] Failed read template files! Cause: %s" % e)
    except KeyError as e:
        fail("[ERROR] Failed to access required field! Cause: %s" % e)
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
    client = docker.from_env()
    app_yml = ctx.obj['APP_YAML']
    tag = "%s/%s" % (app_yml['app']['org'],
                     app_yml['app']['name'])
    img = client.images.build(path=app_dir,
                              tag=("%s:%s" % (tag, app_yml['app']['version'])))
    registry = app_yml['build'].get('registry')
    if registry:
        img.tag(registry, "%s:%s" % (tag, app_yml['app']['version']))
    if latest:
        img.tag(registry, "%s:latest" % tag)


if __name__ == '__main__':
    cli(obj={})
