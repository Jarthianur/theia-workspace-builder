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

## Ideas for features

### Build command

For now the builder tool only prepares the Dockerfile and package.json inside the app directory.
It would be great to also have a command that builds the container with arguments and tags specified in the application.yaml.

### Different base images

For now all workspaces are based on manjaro linux.
While manjaro offers an excellent development environment, a certain base system is often required for a project, or environment.
Hence it would be great to support different common base images, and make them selectable from the application.yaml.
To make this possible, it would be required to provide different setups (Dockerfiles) for each base image and modules.

### Parameterized builds

Sometimes a module could offer optional features, or requires a certain version of something.
For example in the *cpp* module boost is not always needed, and would blow the image size a lot.
Maybe there is a certain language version used for development, which could be passed as argument to the build.
Hence it would be great to allow arguments, or variables in the application.yaml
