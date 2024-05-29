import sys
import subprocess
import yaml

# Pre-Requisites:
class MinVersions:
    BASH = (5,0) # bash --version | grep -Eo '[0-9]\.[0-9]+\.[0-9]+'
    PYTHON = (3,9) # python --version | grep -Eo '[0-9]\.[0-9]+\.[0-9]+'
    COOKIE_CUTTER = (2,0) # cookiecutter --version | grep -Eo '[0-9]\.[0-9]+\.[0-9]+'
    CRUFT = (1,0)
    DOCKER_ENGINE = (20,10,13)
    DOCKER_COMPOSE = (2,20) # docker-compose --version | grep -Eo '[0-9]\.[0-9]+\.[0-9]+'
    DOCKER_IMAGES = ('dioptra/mlflow-tracking',
                     'dioptra/nginx', 
                     'dioptra/pytorch-cpu', 
                     'dioptra/restapi', 
                     'dioptra/tensorflow2-cpu',
                     )
# -------------------------------------------------------------------------------------------------

PROMPT_CMD_BUILD_CONTAINERS = 'make build-nginx build-mlflow-tracking build-restapi build-pytorch-cpu build-tensorflow-cpu'
PROMPT_CMD_BUILD_ALL_CONTAINERS = 'make build-all'
# ---=== OS-Specific Commands Dictionary ===---
OS_CMD_WHICH = {'': 'which', 
                '':'where', 
                '':'Get-Command'
                }
# -------------------------------------------------------------------------------------------------

def get_version_tuple(data: str, ignore_non_int: bool = False) -> tuple:
    """ Parse out the version string into an int-Tuple-comparable entity
    Args:
        data (str): Monolithic string with version information. Assumed to separate version STR by '.' and '-'
        ignore_non_int (bool): [default:False] Replace non-int with -1 (@False) or ignore&skip it (@True)
    Returns:
        tuple:  Version TUPLE of non-predetermined length representing the version information. 
                Warning! The non-int-able STR values are replaced by -1 entries
    """
    version = []
    int_part = -100
    prep = (data.replace('-', '.')).split('.')
    print(prep)
    for version_part in prep:
        try:
            int_part = int(version_part.strip())
        except ValueError:
            if ignore_non_int:
                continue  # Non-INT-parsable string is ignored & skipped
            else:
                int_part = -1  # Non-INT-parsable string becomes int -1
        finally:
            version.append(int_part)
    return tuple(version)
# -------------------------------------------------------------------------------------------------

def is_docker_OK() -> bool:
    """ Verifies that docker is installed and has the acceptable version 
    Returns:
        bool: True if docker version is ACCEPTABLE
    """
    try:
        proc = subprocess.run(['docker', 'version'], encoding='utf-8', stdout=subprocess.PIPE)
        info_ver = proc.stdout
        data = yaml.safe_load(info_ver)
        client_version = get_version_tuple(data['Client']['Version'])
        server_engine_version = get_version_tuple(data['Server']['Engine']['Version'])
    except Exception as ex:
        return False
    finally:
        # Finalize information gathering
        pass
# -------------------------------------------------------------------------------------------------

def is_git_OK() -> bool:
    """ Verifies that docker is installed and has the acceptable version 
    Returns:
        bool: True if docker version is
    """
    try:
        cmd1= ['which', 'git']
        cmd1= ['git', '--version',  '|'," grep -Eo '[0-9]\.[0-9]+\.[0-9]+'"]
        proc = subprocess.run(['which', 'git'], encoding='utf-8', stdout=subprocess.PIPE)
        info_ver = proc.stdout
        data = yaml.safe_load(info_ver)
        client_version = get_version_tuple(data['Client']['Version'])
        server_engine_version = get_version_tuple(data['Server']['Engine']['Version'])
    except Exception as ex:
        return False
    finally:
        # Finalize information gathering
        pass
# -------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    print(f'Verifying that DIOPTRA pre-requisites in your environment are met')
    if is_docker_OK():
        print(f'\tDocker configuration check Passed ✅︎')
    else:
        print(f'\tDocker configuration check Failed ❌')

    
    sys.exit(1)