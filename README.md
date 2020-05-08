# theia-workspace-builder

**This readme currently describes what I want to achieve by this project.**

This is an attempt to unify the creation and provisioning of theia docker workspaces.
It is based on https://github.com/theia-ide/theia-apps, which consists of different example setups for language specific workspaces with eclipse theia IDE.
The idea of this project is to provide all different setups as atomic modules, that can be included into a workspace application.

## how it should look like

In the end it would be great to have a utility script that allows for easy selection of modules, and baking them together into the final docker image.
Therefor we need a directory structure where every directory contains language / environment specific setups and resources, including the installation part for dockerfiles.
To achieve the merge and build process, we need a tool that accepts required flags to specify the wanted environment setup.

## current setup

In the project root are directories inside *modules*.
These modules may contain a

+ Dockerfile
+ package.json

The modules should be designed in a non conflicting way to each other.

To define an application a new directory is created, which contains an **application.yaml** file.
Additionally there may be a Dockerfile and a package.json, where app specific stuff can be included, in a subdirectory called **module**.
Resources like settings.json can be placed there in the app directory.
The provisioning tool takes the base module and interpolates every module specified in the application.yaml into a resulting Dockerfile and package.json.
From there the application can be built using docker cli.

## Current application.yaml layout

```yaml
app:
  name: theia-example
  version: "0.0.4"
  org: my-org
  license: "Apache-2.0"
  title: "Example Theia Application"
  base: manjaro
parameters:
  cpp:
    with_boost: yes
    with_omp: yes
build:
  registry: my-reg
modules:
  - cpp
  - sys-manager
  - python
```

## Currently supported base systems

|Base|Use Case|
|--|--|
|manjaro|Cutting edge development platform.|
