# theia workspace builder

Theia workspace builder (TWB) is an attempt to unify the process of provisioning, and building of development environments featuring [eclipse-theia](https://github.com/eclipse-theia/theia), as docker containers.
*TWB* consists of different atomic setups, so called modules, alongside the actual builder tool.
In short, *TWB* allows to pack those modules together from a simple configuration file into a workspace of your needs.

## How it works

Basically every workspace is broken down into a base system, and independant modules that take of certain languages, or utilities.
Each module provides just the setup steps and dependencies, which are required for its purpose.
By utilizing jinja templates, *TWB* merges the base, and all configured modules into a single workspace setup, which can be built as container.

Every module, and the base setup as well, consists of a system dependent Dockerfile template, and a package.json file.
While all installation and setup steps are placed in the Dockerfile, the package.json contains dependencies and plugins required by theia.
By providing a system dependent Dockerfile, it is possible to support multiple base systems, where you can choose one of in your workspace configuration.

The builder tool is a utility, that does all the work for you, and bundles your workspace setup into a ready-to-use docker image.

## Getting started

An example workspace setup can be found in [example-ws](example-ws/).

### Define a workspace

To define a workspace, all you need to do is to create a directory, and place an *application.yaml* file in there.
It is not important, where you create this directory, but recommended to place it inside your clone of this repository, as it allows the most easy use.
All workspace specific files go in this directory as well.

### The application.yaml

A minimal application.yaml looks like the following.

```yaml
app:
  name: example-ws
  version: "0.0.1"
  org: my-org
  license: "Apache-2.0"
  title: "Example Theia Workspace"
  base: manjaro
modules:
  - ...
```

Apart from *modules*, *app* and all keys under it are mandatory.
While *modules* itself is optional, it would be pointless to have a workspace without any language setup.
To include a module in your workspace, just add it to the list of *modules*.

It is also possible to set parameters for your workspace, and configure even more, like described in []().

### Prepare and build your workspace

There is a python tool in *builder-tool*, which does all that for you.
This tool can either be called directly or first installed via setuptools.
Run it with `--help` to get more information about its usage.

#### Preparation

Run the builder tool with **prepare** command, to generate the final Dockerfile and package.json files inside your workspace definition directory.
The prepare command must always be ran before build.

```bash
python3 builder-tool/main.py prepare example-ws/
```

#### Build

Run the builder tool with **build** command, to build the docker image.
The build command might require *root* permissions, in order to talk to docker daemon.

```bash
python3 builder-tool/main.py build example-ws/
```

### Run your workspace container

In order to run the workspace as container, with support for git over ssh, run something like the following command.

```bash
docker run --init --security-opt seccomp=unconfined -dit --restart=always -p 3000:3000 -v "$(pwd)/my-project/:/home/project:cached" -v "$(pwd)/.ssh:/home/theia/.ssh:ro" user/example-ws
```

## Complete application.yaml schema

## How to create modules

## Currently supported base systems

|Base|Use Case|
|--|--|
|manjaro|Cutting edge development platform.|
