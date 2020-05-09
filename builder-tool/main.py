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


class BuildError(Exception):
    pass


def fail(msg):
    logging.error(msg)
    sys.exit(1)


def resolvePackageJson(fpath, deps, plugs):
    if not Path(fpath).is_file():
        logging.warning("Could not find [%s]." % fpath)
        return
    try:
        with fpath.open('r') as pkg_json:
            pkg = json.load(pkg_json)
            if 'dependencies' in pkg:
                deps.update(pkg['dependencies'])
            if 'theiaPlugins' in pkg:
                plugs.update(pkg['theiaPlugins'])
    except json.JSONDecodeError as e:
        raise PrepareError("Invalid JSON in [%s]! Cause: %s" % (fpath, e))
    except OSError as e:
        raise PrepareError("File at [%s] not readable! Cause: %s" % (fpath, e))


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
    except jinja2.TemplateError as e:
        raise PrepareError(
            "Invalid template, or variables at [%s]! Cause: %s" % (fpath, e))
    except OSError as e:
        raise PrepareError("File at [%s] not writable! Cause: %s" % (fpath, e))


def resolveDockerfile(fpath, scripts, params):
    if not Path(fpath).is_dir():
        logging.warning("Could not find [%s]." % fpath)
        return
    try:
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(
            fpath))
        dock = env.get_template('Dockerfile.j2')
        scripts.append(dock.render(parameters=params))
    except jinja2.TemplateError as e:
        raise PrepareError(
            "Invalid template, or variables at [%s]! Cause: %s" % (fpath, e))


def prepareDockerfile(ctx):
    dock_tmpl = ctx.obj['TMPL_ENV'].get_template('Dockerfile.j2')
    scripts = list()
    app_yml = ctx.obj['APP_YAML']
    app_dir = ctx.obj['APP_DIR']
    params = app_yml.get('parameters') or dict()

    for mod in app_yml.get('modules') or ():
        mod_params = params.get(mod) or dict()
        resolveDockerfile(Path(ctx.obj['MOD_DIR'], 'modules', mod, app_yml['app']['base']).resolve(),
                          scripts, mod_params)

    resolveDockerfile(Path(app_dir, 'module').resolve(),
                      scripts, params.get('module') or dict())

    fpath = Path(app_dir, 'Dockerfile').resolve()
    try:
        with fpath.open('w') as res:
            res.write(dock_tmpl.render(scripts=scripts))
    except jinja2.TemplateError as e:
        raise PrepareError(
            "Invalid template, or variables at [%s]! Cause: %s" % (fpath, e))
    except OSError as e:
        raise PrepareError("File at [%s] not writable! Cause: %s" % (fpath, e))


def initAppDir(ctx, app_dir):
    if 'APP_DIR' in ctx.obj:
        return
    ctx.obj['APP_DIR'] = app_dir
    fpath = Path(app_dir, 'application.yaml').resolve()
    try:
        with fpath.open('r') as app_yaml:
            ctx.obj['APP_YAML'] = yaml.safe_load(app_yaml)
    except (yaml.YAMLError, OSError) as e:
        fail("Failed to parse [%s]! Cause: %s" % (fpath, e))
    try:
        validation.validate(ctx.obj['APP_YAML'])
    except validation.ValidationError as e:
        fail(e)


def cleanAppDir(app_dir):
    try:
        Path(app_dir, 'package.json').resolve(strict=True).unlink()
    except Exception:
        pass
    try:
        Path(app_dir, 'Dockerfile').resolve(strict=True).unlink()
    except Exception:
        pass


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
        logging.info("Successfully prepared '%s' at [%s]. You may now build the container.",
                     ctx.obj['APP_YAML']['app']['name'], ctx.obj['APP_DIR'])
    except (jinja2.TemplateError, OSError) as e:
        cleanAppDir(app_dir)
        fail("Failed to read base template files! Cause: %s" % e)
    except PrepareError as e:
        cleanAppDir(app_dir)
        fail("Failed to prepare the application! Cause: %s" % e)


def buildDockerImage(client, repo, app_dir, app_yml):
    img = None
    try:
        build_cfg = app_yml.get('build') or dict()
        stream = client.build(
            decode=True,
            path=app_dir,
            tag=("%s:%s" % (repo, app_yml['app']['version'])),
            buildargs=build_cfg.get('arguments')
        )
        for chunk in stream:
            if 'stream' in chunk:
                for line in chunk['stream'].splitlines():
                    click.echo(line.rstrip())
            elif 'aux' in chunk:
                img = chunk['aux']['ID']
        if not img:
            raise BuildError("Build returned no image ID!")
    except docker.errors.APIError as e:
        raise BuildError(e)
    return img


def tagDockerImage(client, img, repo, latest, app_yml):
    build_cfg = app_yml.get('build') or dict()
    registry = build_cfg.get('registry')
    try:
        if registry:
            client.tag(img, "%s/%s" % (registry, repo), "%s" %
                       app_yml['app']['version'], force=True)
        if latest:
            client.tag(img, ("%s/%s" % (registry, repo))
                       if registry else repo, "latest", force=True)
    except docker.errors.APIError as e:
        raise BuildError(e)


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
        img = buildDockerImage(client, repo, app_dir, app_yml)
    except OSError:
        fail("Failed to connect to docker daemon!")
    except BuildError as e:
        fail("Failed to build the docker image! Cause: %s" % e)
    logging.info("Successfully built the docker image.")
    try:
        tagDockerImage(client, img, repo, latest, app_yml)
    except OSError:
        fail("Failed to connect to docker daemon!")
    except BuildError as e:
        fail("Failed to tag the docker image! Cause: %s" % e)
    logging.info("Successfully tagged the docker image.")


if __name__ == '__main__':
    cli(obj={})
