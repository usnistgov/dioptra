import logging
import math
import os
import re
import sys
import subprocess
import platform
import yaml


DEBUG=False
def deb(message:str)->None:
    if DEBUG:
        print(f'\tDeb:\t{message}')
# -------------------------------------------------------------------------------------------------
TODO_GUIDE = {'install_tools':[], 'update_tools':[], 
              'make_images':[], 'missing_image_names':[],}
TOOL_VER = {}
# -------------------------------------------------------------------------------------------------

class MinVersions:
    """ Container class of the Min Versions Pre-Requisites:
    """
    INFO_BASH = {'cmd': 'bash', 'ver':(5,0), 
                 'ver_cmd': ["bash", "--version"],
                 'guide': 'Instal Bash Version 5.0+'
                 } # , " grep -Eo '[0-9]\.[0-9]+\.[0-9]+'"
    INFO_PYTHON = {'cmd': 'python', 'ver':(3,9), 
                   'ver_cmd':["python", "--version"],
                 'guide': 'Instal Python Version 3.9 or higher (3.9+)'}
    INFO_COOKIE_CUTTER = {'cmd': 'cookiecutter', 'ver':(2,0), 
                          'ver_cmd': ["cookiecutter" , "--version"],
                          'guide': 'Instal Cookiecutter Version 2.0 or higher (2.0+)'} 
    INFO_DOCKER_ENGINE = {'cmd': 'docker', 'ver':(20,10,13), 'ver_cmd':"",
                          'guide': 'Instal Docker/Rancher Version 20.10.13+'} # YAML+ Parsing
    INFO_DOCKER_COMPOSE = {'cmd': 'docker-compose','ver':(2,20), 
                           'ver_cmd':["docker-compose", "--version"],
                          'guide': 'Instal Docker-Compose Version 2.0 or higher (2.0+)'} 
    LIST_DOCKER_IMAGES = {'list':('dioptra/mlflow-tracking',
                            'dioptra/nginx', 
                            'dioptra/pytorch-cpu', 
                            'dioptra/restapi', 
                            'dioptra/tensorflow2-cpu',
                            ), 
                     'list_cmd': 
                       ["docker","image","ls"], 
                      'title':'Docker containers',
                      'guide':'From the dioptra repository root Directory run the following command: \n\t make build-<image> \n For every of the missing image'
                    }   
    # ??? version of CRUFT is not specified in the docs, or is it ???
    INFO_CRUFT = {'cmd':'cruft', 'ver': (2,0,0), 
                  'ver_cmd': ["cruft", "--help"],
                  'guide': 'Instal Cruft Version 2.0+'} 
    # ??? version of CRUFT is not specified in the docs, or is it ???
    # ---------------------------------------------------------------------------------------------
# =================================================================================================
# ---=== OS-Specific Commands Dictionary ===---
class WhichSelector:

    OS_SPECIFIC_WHICH = {
                'Unix': 'which', 
                'Linux': 'which', 
                'Darwin': 'which', 
                'Windows': 'where', 
                }    
    def get_which() -> str:
        system = platform.system()
        return WhichSelector.OS_SPECIFIC_WHICH[system]
    
# =================================================================================================
PROMPT_CMD_BUILD_CONTAINERS = 'make build-nginx build-mlflow-tracking build-restapi build-pytorch-cpu build-tensorflow-cpu'
PROMPT_CMD_BUILD_ALL_CONTAINERS = 'make build-all'
# =================================================================================================

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
    deb(f'{prep=}')
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
# =================================================================================================

def tool_exists(tool:str) -> tuple[bool, str]:
    """ Verifies that the tool exists in the current environment 

    Args:
        tool (str): tool-name

    Returns:
        tuple[bool, str]: tuple of 0:Tool-Exists as boolean and 1:Sys-Path to the Tool as String
    """
    which_command = WhichSelector.get_which()

    deb(f'{which_command=}')
    deb(f"To run:\n\t{[f'{which_command}', tool]}")

    proc = subprocess.run([f'{which_command}', tool], encoding='utf-8', 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)
    deb(f"{proc.stdout=}\t{proc.stderr}")
    path = proc.stdout.replace("\n", "")
    return (bool(path), path)
# =================================================================================================

def get_tool_version(tool: dict) -> tuple:
    proc = None
    no_ver = (0,0)
    if 'cmd' in tool.keys() and 'ver' in tool.keys() and 'ver_cmd' in tool.keys():
        cmd = tool['ver_cmd']
        ver_pattern = re.compile('[0-9]\.[0-9]+\.[0-9]+')
        sub_data = subprocess.run(cmd, encoding='utf-8', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ver_draft = re.findall(ver_pattern, sub_data.stdout)
        deb(f"{cmd=}=>\n{ver_draft=}")
        ver_list =  ver_draft[0] if hasattr(ver_draft, '__len__') else ver_draft
        deb(f"{cmd=}=>\n{ver_draft=}\t{ver_list=}")
        return get_version_tuple(ver_list, ignore_non_int=True)
    return no_ver
# =================================================================================================

def is_docker_OK() -> tuple[bool, tuple, tuple]:
    """ Verifies that docker is installed and has the acceptable version 
    Returns:
        bool: True if docker version is ACCEPTABLE
    """
    server_engine_version = None
    try:
        proc = subprocess.run(['docker', 'version'], encoding='utf-8', stdout=subprocess.PIPE)
        info_ver = proc.stdout
        data = yaml.safe_load(info_ver)
        # client_version = get_version_tuple(data['Client']['Version'])
        server_engine_version = get_version_tuple(data['Server']['Engine']['Version'])
    except Exception as ex:
        return False
    finally:
        # Finalize information gathering
        return (MinVersions.INFO_DOCKER_ENGINE['ver'] <= server_engine_version, 
                MinVersions.INFO_DOCKER_ENGINE['ver'], 
                server_engine_version)
# =================================================================================================

def check_docker_images(list_data) -> tuple[bool, list, list]:
    """ Verifies that docker is installed and has the acceptable version 
    Returns:
        bool: True if docker version is ACCEPTABLE
    """
    absent = []
    present = []
    try:
        dims = list_data['list']
        cmd = list_data['list_cmd']
        proc = subprocess.run(cmd, encoding='utf-8', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        images_bulk = proc.stdout.split("\n")
        entries = { list(map(str.strip, y.split(' ')))[0]: 
                    list(map(str.strip, y.split(' '))) 
                   for y in images_bulk if y.startswith('dioptra/')}
        
        images = entries.keys()
        for image in dims:
            if not image in images:
                absent.append(image)
            else:
                present.append(image)
    except Exception as ex:
        return False
    finally:
        # Finalize information gathering
        return (len(absent) <= 0, 
                absent, 
                present)
# =================================================================================================
# =================================================================================================

class Prompts:
    """ Aggregated prompts to unify UI looks and color all at once if needed
    """
    class Text:
        BLACK='\033[30m'
        RED='\033[31m'
        GREEN='\033[32m'
        ORANGE='\033[33m'
        BLUE='\033[34m'
        PURPLE='\033[35m'
        CYAN='\033[36m'
        LIGHT_GREY='\033[37m'
        DARK_GREY='\033[90m'
        LIGHT_RED='\033[91m'
        LIGHT_GREEN='\033[92m'
        YELLOW='\033[93m'
        LIGHT_BLUE='\033[94m'
        PINK='\033[95m'
        LIGHT_CYAN='\033[96m'
        # ---------------------------
        BOLD='\033[01m'
        RESET='\033[0m'
    # ---------------------------------------------------------------------------------------------
    info_width = 80
    start_space = ' '*2
    alert_width = 80
    alert_symbol = '#'
    status_OK = f'  {Text.GREEN}Check Passed ✅︎{Text.RESET}'
    status_Failed = f' {Text.RED}{Text.BOLD}Check Failed ❌{Text.RESET}\n'
    char_OK = "✅︎"
    char_Fail = "❌"
    char_TODO = "❗"
    filler = '.' if DEBUG else " "
    # ---------------------------------------------------------------------------------------------
    def print_message(info_part: str, status_part: str, text_mod: str = '') -> None:
        if not text_mod:
            info_msg = info_part + Prompts.filler*(Prompts.info_width-len(info_part))
        else:
            info_msg = (f"{text_mod}{info_part}"
                        f"{Prompts.filler*(Prompts.info_width-len(info_part))}"
                        f"{Prompts.Text.RESET}"
                       )
        print(f'{info_msg}{status_part}')
    # ---------------------------------------------------------------------------------------------

    def print_alert(alert_info: str, a_symbol: str = None, text_mod: str = None) -> None:
        """ Prints alert message
        Args:
            alert_info (str): Alert message to print
            a_symbol (str, optional): Alert symbol. Defaults to None, 
                                    which resolves to value of Prompts.alert_symbol.
            text_mod (str, optional): Text modifier: color, boldness, etc. Defaults to None.
        """
        alert_status = ''
        alert_char = Prompts.alert_symbol if not a_symbol else a_symbol
        ap_len=len(alert_char)
        if not text_mod:
            info_msg = (alert_info + 
                        Prompts.filler*(Prompts.info_width-len(alert_info))
                        )
        else:
            info_msg = (f"{text_mod}{alert_info}"
                        f"{Prompts.filler*(Prompts.info_width-len(alert_info))}"
                        f"{Prompts.Text.RESET}"
                       )
        print(f'{info_msg}{alert_status}')
    # ---------------------------------------------------------------------------------------------

    def check_docker_version(tool: dict) -> None:
        (is_version_OK, need_ver, have_ver) = is_docker_OK()
        if is_version_OK:
            Prompts.print_message(
                info_part = f"{Prompts.start_space}✅︎ {tool['cmd'].capitalize()} version v{have_ver} >= v{need_ver}",
                status_part = Prompts.status_OK, 
                text_mod=f"{Prompts.Text.LIGHT_GREEN}"
                )
        else:
            Prompts.print_message(
                info_part = f"\n\t❌ {tool['cmd'].capitalize()} ❌ version is {have_ver} not >= {need_ver}", 
                status_part = Prompts.status_Failed, 
                text_mod=f"{Prompts.Text.PINK}{Prompts.Text.BOLD}"
                )    
        # ---------------------------------------------------------------------------------------------

    def prompt_not_found(tool: str) -> None:
        """ Shaping messages for not which/where found commands
        Args:
            command (str): name of the command
        """
        Prompts.print_message(
            info_part = (   f'\n{Prompts.start_space}❌ {tool.capitalize()}'
                            f' ❌{Prompts.start_space}is not found or is not on PATH!'), 
            status_part = Prompts.status_Failed, 
            text_mod=f"{Prompts.Text.PINK}{Prompts.Text.BOLD}"
            )
    # ---------------------------------------------------------------------------------------------

    def prompt_exists(tool: str, path: str) -> None:
        """ Shapes and prints message for successfully found command 
        Args:
            command (str): name of the command
        """
        Prompts.print_message(
            info_part = f'{Prompts.start_space}✅︎ {tool.capitalize()} exists @{path}',
            status_part = Prompts.status_OK, 
            text_mod=f"{Prompts.Text.LIGHT_GREEN}"
        )
    # ---------------------------------------------------------------------------------------------

    def check_tool_exists(tool: dict, display_info: bool = True) -> bool:
        """ Checks if the tool exists and prints result status in terminal
        Args:
            tool_name (str): tool-name (e.g. 'bash' or 'docker')
        """
        if 'cmd' in tool.keys():
            tool_name = tool['cmd']
            (exists, path) = tool_exists(tool_name)
            if exists:
                if  display_info:
                    Prompts.prompt_exists(tool_name, path)
                return True
            else:
                if  display_info:
                    Prompts.prompt_not_found(tool_name)
                    TODO_GUIDE['install_tools'].append(tool)
            return False
    # ---------------------------------------------------------------------------------------------

    def prompt_version_old(tool: dict, have_ver: tuple) -> None:

        Prompts.print_message(
            info_part =(f"\n{Prompts.start_space}❌ {tool['cmd'].capitalize()}"
                        f" ❌{Prompts.start_space}version is {have_ver} not >= {tool['ver']}"),
            status_part = Prompts.status_Failed, 
            text_mod=f"{Prompts.Text.PINK}{Prompts.Text.BOLD}"
            )
    # ---------------------------------------------------------------------------------------------
    def prompt_tool_title(tool_name: str):
        if tool_name:
            print(f"\n{tool_name.capitalize()} check:")
        else:
            print(f"\n{'Unexpected'.capitalize()} check:")

    # ---------------------------------------------------------------------------------------------
    def prompt_version_OK(tool: dict, have_ver: tuple) -> None:
        Prompts.print_message(
            info_part = f"{Prompts.start_space}✅︎ {tool['cmd'].capitalize()} version v{have_ver} >= v{tool['ver']}",
            status_part = Prompts.status_OK, 
            text_mod=f"{Prompts.Text.LIGHT_GREEN}"
        )
    # ---------------------------------------------------------------------------------------------

    def check_tool_version(tool: dict) -> None:
        if 'ver' in tool.keys():
            have_version = get_tool_version(tool)
            deb(f"{have_version=}  ???>=??? {tool['ver']=}")
            if  tool['ver'] <= have_version:
                Prompts.prompt_version_OK(tool, have_version)
            else:
                Prompts.prompt_version_old(tool, have_version)
                TODO_GUIDE['update_tools'].append(tool)
        else:
            Prompts.print_message(
            info_part = f'\n\t{tool.capitalize()} had no required version!', 
            status_part = Prompts.status_Failed, 
            info_mod=f"{Prompts.Text.PINK}{Prompts.Text.BOLD}"
            )
    # ---------------------------------------------------------------------------------------------

    def verify_docker_images(docker_images : dict) -> None:
        (ok, missing, present)=check_docker_images(MinVersions.LIST_DOCKER_IMAGES)
        tool_msg = f"all {docker_images['title']}".capitalize()
        if ok:
            Prompts.print_message(
                info_part = (   f'{Prompts.start_space}'
                                +f'✅︎  {tool_msg} exist'),
                status_part = Prompts.status_OK, 
                text_mod=f"{Prompts.Text.LIGHT_GREEN}"  )
        else:
            TODO_GUIDE['make_images'].append(docker_images['guide'])
            TODO_GUIDE['missing_image_names'].extend(missing)
    # ---------------------------------------------------------------------------------------------

    def prompt_todo_header(name_todo: str) -> None:
        """ Generate Header for the TODO LIST
        Args:
            name_todo (str): Todo entry name e,g, "install_tools", "upgrade_tools"
        """
        def get_margins(msg: str)->tuple[int, int]:
            """ (LOCAL) Message centering margins compute
            Args:
                msg (str): The message to center
            Returns:
                tuple[int, int]: (left, right) margins
            """
            dw = Prompts.alert_width - len(msg)
            return (dw//2, math.ceil(dw/2))
            #------------------------------------------
        if name_todo in ['install_tools', 'update_tools'] :
            msg = f"{Prompts.start_space}You need to {name_todo.replace('_', ' the following ')}:{Prompts.start_space}"
        elif name_todo in ['make_images', 'missing_image_names']:
            pass
        else:
            pass
        color = Prompts.Text.PURPLE
        left, right = get_margins(msg)
        line = (    f"{Prompts.Text.BOLD}{color}"+
                    f"{Prompts.alert_symbol*Prompts.alert_width}"+
                    f"{Prompts.Text.RESET}" 
                )
        prefix = Prompts.alert_symbol*left
        suffix = Prompts.alert_symbol*right
        header = (  f'\n\n{line}'
                    +f"\n{Prompts.Text.BOLD}{color}{prefix}{Prompts.Text.RESET}"
                    +f'{msg}'
                    +f"{Prompts.Text.BOLD}{color}{suffix}{Prompts.Text.RESET}"
                    +f'\n{line}\n'
                 )
        Prompts.print_alert( header )
    # ---------------------------------------------------------------------------------------------

    def prompt_todo_item(item: str)->None:
        print(item)    
    # ---------------------------------------------------------------------------------------------

    def prompt_todo() -> None:
        prefix = f"{Prompts.start_space}{Prompts.char_TODO} "
        for name_todo,items_todo in TODO_GUIDE.items():
            if len(items_todo)>0:
                Prompts.prompt_todo_header(name_todo)
                for index, entry in enumerate(items_todo,1):
                    if name_todo in ['install_tools','update_tools'] :
                        if 'guide' in entry.keys():
                            Prompts.prompt_todo_item(
                                f"{prefix}{index}.\t{entry['guide']}"
                                )
                        elif 'cmd' in entry.keys() and 'ver' in entry.keys():
                            Prompts.prompt_todo_item(
                                f"{prefix}{index}.\tInstall the {entry['cmd']} of the version {entry['ver']}"
                                )
                        elif 'cmd' in entry.keys():
                            Prompts.prompt_todo_item(
                                f"{prefix}{index}.\tInstall the {entry['cmd']}"
                                )
                        else:
                            # Something weird in the description dictionary of the tool/check
                            pass
                    elif name_todo == 'make_images':
                        Prompts.prompt_todo_item(f"")
    # ---------------------------------------------------------------------------------------------
# =================================================================================================



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(f'\nVerifying that DIOPTRA pre-requisites in your environment are met')
  
    s = [f"{getattr(MinVersions,x)['cmd']}>={getattr(MinVersions,x)['ver']}"  
         for x in dir(MinVersions) 
         if x.startswith('INFO_') and 'cmd' in getattr(MinVersions,x).keys() and  'ver' in getattr(MinVersions,x).keys()]
    deb(s)

    # ==-- Non-linear/Looping Pre-Req Verification --==
    required_tools = [getattr(MinVersions,x) for x in dir(MinVersions) if x.startswith('INFO_')]
    # ==- Loop over the INFO_* tools --==
    for tool in required_tools:
        if 'cmd' in tool.keys():
            Prompts.prompt_tool_title(tool['cmd'])
            if str(tool['cmd']).lower()!='docker' :
                if Prompts.check_tool_exists(tool):
                    Prompts.check_tool_version(tool)
            elif str(tool['cmd']).lower()=='docker':
                # ==-- docker version check --==  
                if Prompts.check_tool_exists(tool):
                    Prompts.check_docker_version(tool)
            else:
                # Error in description 
                print(tool) 
        else:
            print('\tRequirements for: \n\t{tool}\n\t were not clearly specified')
            
    # ==-- Docker-containers list check --==  
    if MinVersions.LIST_DOCKER_IMAGES:
        if ( 'list' in MinVersions.LIST_DOCKER_IMAGES.keys()
            and 'list_cmd' in MinVersions.LIST_DOCKER_IMAGES.keys() ):
            if Prompts.check_tool_exists(MinVersions.INFO_DOCKER_ENGINE, display_info = False):
                Prompts.prompt_tool_title(MinVersions.LIST_DOCKER_IMAGES['title'])
                Prompts.verify_docker_images(MinVersions.LIST_DOCKER_IMAGES)

    # ==-- Summarize the needed installs/updates/upgrades/container builds --==
    if len(TODO_GUIDE.keys())>0:
        # ==-- Nicely Print Guidance Summary of What Was Found Lacking --==
        Prompts.prompt_todo()
        # ==-- Also stop running the template with CookieCutter/or CRUFT --==
        sys.exit( len(TODO_GUIDE.keys()) )

