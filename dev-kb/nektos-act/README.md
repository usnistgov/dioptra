# Nektos-ACT Use Guide
## The guide describes use of Nektos-ACT for developing, debugging, and running github actions locally

# [ACT by Nektos](https://nektosact.com/introduction.html) for developers.
 - [How to install ACT](#act-install)
 - [How to verify installation ACT](#act-verify)
   - [How to query act version](#act-version) 
   - [How to list available files, jobs and workflows](#act-jobs) 
   - [How to graph workflow](#act-graph)
 - [Optional environment setup for ACT with Rancher and Custom Docker](#act-env)
 - [How to run and test github actions and workflows locally](#act-run)

---

## <a id="act-install"> [Installation of ACT](https://nektosact.com/installation/index.html) can be shortly described as:</a>

### Macos - Homebrew
```sh
brew install act
```

### MacOS - Port
```sh
sudo port install act
```

### Ubuntu - Pre-Built Install
```sh
curl --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

---
## <a id="act-verify"> To verify success of the ACT installation you can run any of the following commands</a>:
 - ### <a id="act-version">List current ACT version</a>:
```sh
act --version
```
Resulting output will look similar to the following:
```sh
▷ act version 0.2.71
```

 - ### <a id="act-jobs"> List of available github actions(jobs) and workflows</a>:
```sh
act --list
```
 The result will look similar to the following:
 ```sh
▷ 
Stage  Job ID                          Job name                        Workflow name         Workflow file      Events                    
0      build-docker-dioptra-apps       build-docker-dioptra-apps       Docker images         docker-images.yml  schedule,push,pull_request
0      pip-compile-aarch64             pip-compile-aarch64             pip-compile runs      pip-compile.yml    schedule                  
0      pip-compile                     pip-compile                     pip-compile runs      pip-compile.yml    schedule                  
0      pip-compile-containers          pip-compile-containers          pip-compile runs      pip-compile.yml    schedule                  
0      docs                            docs                            Sphinx documentation  sphinx-docs.yml    push                      
0      unit-tests                      unit-tests                      Tox tests             tox-tests.yml      push                      
0      linting-and-style-checks        linting-and-style-checks        Tox tests             tox-tests.yml      push                      
1      consolidate-requirements-files  consolidate-requirements-files  pip-compile runs      pip-compile.yml    schedule   
```

 - ### <a id="act-graph"> Graph the actions(jobs)</a>:
```sh
act --graph
```
``` 
▷ 
 ╭───────────────────────────╮ ╭─────────────╮ ╭────────────────────────╮ ╭─────────────────────╮ ╭──────╮ ╭────────────╮ ╭──────────────────────────╮
 │ build-docker-dioptra-apps │ │ pip-compile │ │ pip-compile-containers │ │ pip-compile-aarch64 │ │ docs │ │ unit-tests │ │ linting-and-style-checks │
 ╰───────────────────────────╯ ╰─────────────╯ ╰────────────────────────╯ ╰─────────────────────╯ ╰──────╯ ╰────────────╯ ╰──────────────────────────╯
                                                                          ⬇
                                                          ╭────────────────────────────────╮
                                                          │ consolidate-requirements-files │
                                                          ╰────────────────────────────────╯
```

---
## <a id="act-env"> Before Running ACT start your container environment (Docker or Rancher)</a>

### For ❗Rancher Desktop❗ or ❗non-default Docker configurations❗ [set DOCKER_HOST](https://nektosact.com/missing_functionality/docker_context.html) environment variable:
 - #### Do this in the same terminal where you plan to use ACT before running ACT.
```sh
export DOCKER_HOST=$(docker context inspect --format '{{.Endpoints.docker.Host}}')
```
### For ❗hosts requiring certificates❗[set DOCKER_CERT_PATH](https://nektosact.com/missing_functionality/docker_context.html) environment variable:
 - #### Do this ONLY if your host requires certificates.
```
export DOCKER_CERT_PATH=$(docker context inspect --format '{{.Storage.TLSPath}}')/docker
```  
 
<!--
<details>
    <summary>MacOS - Brew</summary>
```sh
sudo port install act
```
</details>
<details>
    <summary>MacOS - Port</summary>
```sh
sudo port install act
```
</details>
<details>
  <summary>Ubuntu</summary>
```sh
curl --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```
</details>
 -->


---
## <a id="act-run"> Run desired github workflow or job locally</a> 

 - ### Either using the workflow filename (e.g. tox-tests.yml) to run all jobs in file:
```sh
act -W ".github/workflows/tox-tests.yml" --container-architecture linux/amd64
```

 - ### Or using the job name (e.g. linting-and-style-checks) to run only a particular part of the YAML file:
```sh
act -j linting-and-style-checks --container-architecture linux/amd64
```