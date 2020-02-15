# nittymcpick

Your friendly nitpicking GitLab bot

## Purpose

This bot does run custom linting tools on receiving a webhook from GitLab and reporting back its findings as comments to the merge request diff

## Prerequisites

* python 3.7+
* GitLab CE/EE

## Setup

### Install tool to a machine

This machine has to be reachable by the GitLab server via network.
In the following we will assume a local installation on the GitLab Server itself (`127.0.0.1`)

* Install via pypi

  ``` shell
  pip3 install nittymcpick
  ```

### Create a GitLab user

* Go to GitLab with an account that can create users (e.g. `root`)
  * **admin/users/new**
    * __Name__ = Nitty McPick
    * __Username__ = nittymcpick
    * __Email__ = foo@localhost (or any other non-exisiting mail address)
    * __Access Level__ = Regular
  * **admin/users/nittymcpick/impersonation_tokens**
    * __Name__ = e.g. Nitty McPick Bot
    * __Scopes__ = **api**, **read_repository**
    * **IMPORTANT** copy the content pof **Your New Impersonation Token**

### Add bot to the project

* Goto Gitlab with an account that can change project settings
  * **[username]/[project]/-project_members/**
    * search __Nitty McPick__ at **GitLabd member or Email address*
    * click **Invite**
    * Change level __Nitty McPick__ from **Guest** to **Reporter**

### Create a GitLab webhook

* Goto Gitlab with an account that can change project settings
  * **[username]/[project]/-/settings/integrations
    * __URL__: http://127.0.0.1:8888
    * __Trigger__: Merge requests events
    * __SSL verification__: uncheck the box
    * Click on **Add webhook**

### Create a configuration for the bot

Create a json file like shown at [config.json.sample](config.json.sample).
The file can contain any number of items

#### `linter` section

 attribute               | description
------------------------ | --------------------------------------------------------------------------------------------------------
name                     | name of the linting tool
path                     | absolute path of binary of the linting tool
args                     | list of additional arguments to be passed to the linter
ret_regex                | regular expression for evaluation of the output of the linter (see [Return Regex](#return-regex))
tweaks.line_count_adjust | Add number of lines to the reported output line number
tweaks.single_file_exec  | Run each matching file in a single linter instance, otherwise all files will be run by a single instance

#### `matches` section

attribute | description
--------- | ---------------------------------------------------
pattern   | Regular expression for files that should be checked

##### Return Regex

The regular expression to extract all the needed data should contain the following named groups

* `severity` - for the severity of the finding (optional)
* `line` - Line where the findings occured
* `message` - A meaningful message
* `file` - The file where the of the finding

### Run the tool

```text
usage: nittymcpick [-h] [--token TOKEN] [--onlynew] [--nowip] [--host HOST]
                    [--port PORT]
                    gitlab botname config

Your friendly linting bot for gitlab

positional arguments:
  gitlab         Url of the gitlab server. E.g. http://foo.bar.corp.com
  botname        Username of the bot in GitLab
  config         config file

optional arguments:
  -h, --help     show this help message and exit
  --token TOKEN  Access token to use (default:GL_ACCESS_TOKEN from environment)
  --onlynew      Comment only on changes (default:false)
  --nowip        Ignore WIP merge requests (default:false)
  --host HOST    IP to bind to (default:127.0.0.1)
  --port PORT    Port to bind to (default:8888)
```

e.g. run

```shell
export GL_ACCESS_TOKEN=<Impersonation Token from gitlab>
nittymcpick http://mygitlab.corp.com nittymcpick config.json
```

now everytime a merge request is opened or changed the tool will run all the configured linting tools.
On a finding it would comment directly to the MR like this

```text
Nitty McPick @nittymcpick · just now
Reporter

mytool found a potential error - the code is absolutely insecure
```

## Docker

There is an already prepared container available under `privkweihmann/nittymcpick:latest`
