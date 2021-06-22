# theia-workspace-builder

Theia workspace builder (TWB) unifies the provisioning and building process of development environments featuring [eclipse-theia](https://github.com/eclipse-theia/theia), as docker containers.
_TWB_ consists of different modular setups, alongside the actual builder tool.
In short, _TWB_ allows to pack those modules together from a simple configuration file into a workspace of your needs.

- [theia-workspace-builder](#theia-workspace-builder)
  - [How it works](#how-it-works)
  - [Getting started](#getting-started)
    - [Define a Workspace](#define-a-workspace)
    - [The application.yaml](#the-applicationyaml)
    - [Prepare and build your Workspace](#prepare-and-build-your-workspace)
      - [Preparation](#preparation)
      - [Build](#build)
    - [Run your Workspace Container](#run-your-workspace-container)
  - [Complete application.yaml Schema](#complete-applicationyaml-schema)
  - [How to create Modules](#how-to-create-modules)
  - [Supported Base Systems](#supported-base-systems)
  - [Versioning](#versioning)
  - [Support Matrix](#support-matrix)
    - [Legend](#legend)

## How it works

Basically every workspace is broken down into a base system, and independant modules that take care of certain languages, or utilities.
By utilizing templates, _TWB_ merges the base and all selected modules into a single workspace setup, which is built as docker image.

Every module, and the base setup as well, consists of a Dockerfile template, and a package.json file.
While all installation steps are placed in the Dockerfile, the package.json contains dependencies and plugins required by theia.
By providing a Dockerfile for each base, it is possible to support multiple systems, where you can choose one of in your workspace configuration.

The builder tool is a utility, that does all the work for you.
It bundles your workspace setup into a ready-to-use docker image.

## Getting started

An example workspace setup can be found in [example-ws](example-ws/).

### Define a Workspace

To define a workspace, all you need to do is to create a directory, and place an _application.yaml_ file in there.
It is not important, where you create this directory, but recommended to place it inside your clone of this repository, as it allows the most easy use.
All workspace specific files stay in this directory as well.

A workspace directory may contain a subdirectory named _module_, where a custom package.json and Dockerfile.j2 can be placed.
This allows to add workspace specific setups.

### The application.yaml

A minimal application.yaml looks like the following.

```yaml
app:
  version: "0.0.1"
  org: my-org
  license: "Apache-2.0"
  title: "Example Theia Workspace"
  base: archlinux
modules:
  - builtin
```

To include a module in your workspace, just add it to the list of _modules_.
It is also possible to set parameters for your workspace.

### Prepare and build your Workspace

The tool that is used to provide workspace setups is found in [builder-tool](builder-tool/).
It can either be invoked directly as python script, or installed via setuptools.
Run it with `--help` to get more information about its usage.

#### Preparation

Run the builder tool with **prepare** command, to generate the final Dockerfile and package.json files inside your workspace directory.
The prepare command must always be ran before build.

```bash
python3 builder-tool/main.py prepare example-ws/
```

If dependencies or plugins are defined multiple times in several package.json files, a warning will be emitted on value changes.
The final value in the resulting package.json depends on module precedence.
The precedences are as follows, where the last entry has the lowest precedence.

- workspace-dir/module/package.json
- modules/.../package.json
- base/package.json

The Dockerfile templates are appended as is, in following order.

- base/_system_/Dockerfile.j2
- modules/.../_system_/Dockerfile.j2
- _workspace_/module/Dockerfile.j2

#### Build

Run the builder tool with **build** command, to build the docker image.
The build command might require _root_ permissions, in order to talk to the docker daemon.

```bash
python3 builder-tool/main.py build example-ws/
```

### Run your Workspace Container

In order to run the workspace as container, with support for git over ssh, run something like the following command.

```bash
docker run --init --security-opt seccomp=unconfined -dit --restart=always -p 3000:3000 -v "$(pwd)/my-project/:/home/project:cached" -v "$(pwd)/.ssh:/home/theia/.ssh:ro" my-org/example-ws
```

## Complete application.yaml Schema

In the below schema, `//` is used as comment, and everything in `()` is optional.

```
app:
  (name): <docker image / theia app name>
  version: <version string>
  org: <organisation name>
  license: <license name>
  title: <application title>
  base: <base system name>
  (base_tag): <base system tag, default is 'latest'>
  (dep_version): <theia dependencies version, default 'latest'>
(parameters): // map module names to their params
  (<module name>):
    <key-value entries for params used in template>
(build):
  (registry): <docker registry name>
  (arguments): // args passed to docker build
    <key-value entries>
(modules):
  <list of module names>
```

If no app name is given, it will be generated from app title by replacing spaces with dashes (`-`) and convert characters to lower (`a-z`).

## How to create Modules

Every module has its own directory under _modules_, where the directory name denotes the module name.
A module may contain a _package.json_ file, with `dependencies` and `theiaPlugins`.
A module may contain subdirectories named after the base system, which may contain one _Dockerfile.j2_.
This Dockerfile template defines all installation steps for this module.
Ideally a module contains also a readme file, to describe its purpose, and parameters.

## Supported Base Systems

- archlinux
- debian

## Versioning

In order to reflect the builder-tools version and the project version, the following schema is applied to git tags.

```
v<project version>@<builder-tool version>
```

Changes in the builder-tool are only reflected in its own version tag, while changes to modules or docs are reflected in the project version tag.
Semantic versioning is used for both.

## Support Matrix

| Base System /<br>Module                            | archlinux |   debian |  ubuntu |
| -------------------------------------------------- | --------: | -------: | ------: |
| [**builtin**](modules/builtin/README.md)           |  &#10003; | &#10003; | &#8210; |
| [**coffeescript**](modules/coffeescript/README.md) |   &#8210; |  &#8210; | &#8210; |
| [**csharp**](modules/csharp/README.md)             |   &#8210; |  &#8210; | &#8210; |
| [**go**](modules/go/README.md)                     |  &#10003; |   &#126; | &#8210; |
| [**hlsl**](modules/hlsl/README.md)                 |   &#8210; |  &#8210; | &#8210; |
| [**java**](modules/java/README.md)                 |   &#8210; |  &#8210; | &#8210; |
| [**lua**](modules/lua/README.md)                   |   &#8210; |  &#8210; | &#8210; |
| [**php**](modules/php/README.md)                   |   &#8210; |  &#8210; | &#8210; |
| [**python**](modules/python/README.md)             |  &#10003; |   &#126; | &#8210; |
| [**razor**](modules/razor/README.md)               |   &#8210; |  &#8210; | &#8210; |
| [**rust**](modules/rust/README.md)                 |  &#10003; |   &#126; | &#8210; |
| [**swift**](modules/swift/README.md)               |   &#8210; |  &#8210; | &#8210; |
| [**vb**](modules/vb/README.md)                     |   &#8210; |  &#8210; | &#8210; |
| [**clojure**](modules/clojure/README.md)           |   &#8210; |  &#8210; | &#8210; |
| [**cpp**](modules/cpp/README.md)                   |  &#10003; | &#10003; | &#8210; |
| [**fsharp**](modules/fsharp/README.md)             |   &#8210; |  &#8210; | &#8210; |
| [**groovy**](modules/groovy/README.md)             |   &#8210; |  &#8210; | &#8210; |
| [**html-css**](modules/html-css/README.md)         |   &#8210; |  &#8210; | &#8210; |
| [**js**](modules/js/README.md)                     |   &#8210; |  &#8210; | &#8210; |
| [**objective-c**](modules/objective-c/README.md)   |   &#8210; |  &#8210; | &#8210; |
| [**pkg-manager**](modules/pkg-manager/README.md)   |  &#10003; | &#10003; | &#8210; |
| [**r**](modules/r/README.md)                       |   &#8210; |  &#8210; | &#8210; |
| [**ruby**](modules/ruby/README.md)                 |   &#8210; |  &#8210; | &#8210; |
| [**shaderlab**](modules/shaderlab/README.md)       |   &#8210; |  &#8210; | &#8210; |
| [**themes**](modules/themes/README.md)             |  &#10003; | &#10003; | &#8210; |
| [**web-utils**](modules/web-utils/README.md)       |   &#8210; |  &#8210; | &#8210; |

### Legend

&#10003;: Fully tested and actively maintained<br>
&#126;: Roughly tested and sporadically maintained<br>
&#8210;: Only builtin plugins
