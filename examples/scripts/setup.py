import yaml
from pathlib import Path
from typing import Any

from dioptra.client import DioptraClient, connect_json_dioptra_client

basic_types = ['integer', 'string', 'number', 'any', 'boolean', 'null']

def create_or_get_experiment(
    client: DioptraClient[dict[str, Any]], 
    group: int, 
    name: str, 
    description: str, 
    entrypoints: list[int]
):
    found = None
    for exp in client.experiments.get(search=name, page_length=100000)['data']:
        if exp['name'] == name:
            found = exp
    if (found != None):
        client.experiments.entrypoints.create(
            experiment_id=found['id'], 
            entrypoint_ids=entrypoints
        )
        return found
    else:
        return client.experiments.create(group_id=group, name=name, description=description, entrypoints=entrypoints)

def create_or_get_entrypoints(
    client: DioptraClient[dict[str, Any]], 
    group: int, 
    name: str, 
    description: str, 
    taskGraph: str, 
    parameters: list[dict[str, Any]], 
    queues: list[int], 
    plugins: list[int]
):
    found = None
    for entrypoint in client.entrypoints.get(search=name, page_length=100000)['data']:
        if entrypoint['name'] == name:
            found = entrypoint
    if (found != None):
        client.entrypoints.modify_by_id(
            entrypoint_id=found['id'], 
            name=name, 
            description=description, 
            task_graph=taskGraph, 
            parameters=parameters, 
            queues=queues
        )
        client.entrypoints.plugins.create(entrypoint_id=found['id'], plugin_ids=plugins)
        return found
    else:
        return client.entrypoints.create(group, name, description, taskGraph, parameters, queues, plugins)

def create_or_get_plugin_type(
    client: DioptraClient[dict[str, Any]], 
    group: int, 
    name: str, 
    description: str, 
    structure: dict[str, Any]
) -> dict[str, Any]:
    ret = None
    for pt in client.plugin_parameter_types.get(page_length=100000)['data']:
        if (pt['name'] == name):
            ret = pt
    if (ret is None):
        ret = client.plugin_parameter_types.create(group_id=group, name=name, description=description, structure=structure)
    return ret

def find_plugin_type(
    client: DioptraClient[dict[str, Any]], 
    name: str, 
    types: dict[str, Any]
) -> dict[str, Any]:
    for t in types.keys():
        if t == name:
            return create_or_get_plugin_type(client, 1, name, name, types[t])['id']
    for t in basic_types:
        if t == name:
            return create_or_get_plugin_type(client, 1, name, 'primitive', {})['id']
    print("Couldn't find type", name, "in types definition.")
    return {}

def create_or_get_queue(
    client: DioptraClient[dict[str, Any]], 
    group: int, 
    name: str, 
    description: str
):
    ret = None
    for queue in client.queues.get(page_length=100000)['data']:
        if queue['name'] == name:
            ret = queue
    if (ret is None):
        ret = client.queues.create(group, name, description)
    return ret

def plugin_to_py(plugin: str):
    return '../task-plugins/' + '/'.join(plugin.split('.')[:-1]) + '.py'

def create_inputParam_object(
    client: DioptraClient[dict[str, Any]], 
    inputs: list[dict[str, Any]], 
    types: dict[str, Any]
):
    ret = []
    for inp in inputs:
        if 'name' in inp:
            inp_name = inp['name']
            inp_type: str = inp['type']
        else:
            inp_name = list(inp.keys())[0]
            inp_type: str = inp[inp_name]
        if 'required' in inp:
            inp_req = inp['required']
        else:
            inp_req = True
        plugin_type = find_plugin_type(client, inp_type, types)
        ret += [{
           'name': inp_name,
           'parameterType': plugin_type,
           'required': inp_req
        }]
    return ret

def create_outputParam_object( 
    client: DioptraClient[dict[str, Any]], 
    outputs: list[dict[str, str]], 
    types: dict[str, Any]
):
    ret = []
    for outp in outputs:
        outp_name = list(outp.keys())[0]
        outp_type: str = outp[outp_name]
        plugin_type = find_plugin_type(client, outp_type, types)
        ret += [{
           'name': outp_name,
           'parameterType': plugin_type,
        }]
    return ret

def read_yaml(filename: str) -> dict[str, Any]:
    with open(filename) as stream:
        try:
            ret = yaml.safe_load(stream)
            return ret
        except yaml.YAMLError as exc:
            print(exc)
    return {}

def register_basic_types(
    client:  DioptraClient[dict[str, Any]], 
    declared: dict[str, Any]
):
    for q in basic_types:
        type_def = create_or_get_plugin_type(client, 1, q, 'primitive', {})
    for q in declared:
        type_def = create_or_get_plugin_type(client, 1, q, 'declared', declared[q])

def get_plugins_to_register(
    client: DioptraClient[dict[str, Any]], 
    yaml_file: str, 
    plugins_to_upload: dict[str, Any] | None = None
):
    plugins_to_upload = {} if plugins_to_upload is None else plugins_to_upload
    yaml = read_yaml(yaml_file)
    task_graph = yaml['graph']
    plugins = yaml['tasks']
    types = yaml['types']
    
    register_basic_types(client, types)

    for plugin in plugins:
        name = plugin
        definition = plugins[plugin]
        python_file = plugin_to_py(definition['plugin'])
        upload = {}
        upload['name'] = name
        if 'inputs' in definition:
            inputs = definition['inputs']
            upload['inputParams'] = create_inputParam_object(client, inputs, types)
        else:
            upload['inputParams'] = []
        if 'outputs' in definition:
            outputs = definition['outputs']
            upload['outputParams'] = create_outputParam_object(client, outputs, types)
        else:
            upload['outputParams'] = []
        if (python_file in plugins_to_upload):
            plugins_to_upload[python_file] += [upload]
        else:
            plugins_to_upload[python_file] = [upload]
    return plugins_to_upload

def create_or_get_plugin(
    client: DioptraClient[dict[str, Any]], 
    group: int, 
    name: str, 
    description: str
):
    ret = None
    for plugin in client.plugins.get(search=name, page_length=100000)['data']:
        if plugin['name'] == name:
            ret = plugin
    if (ret is None):
        ret = client.plugins.create(group_id=group, name=name, description=description)
    return ret

def create_or_modify_plugin_file(
    client: DioptraClient[dict[str, Any]], 
    plugin_id: int, 
    filename: str, 
    contents: str, 
    description: str, 
    tasks: list[dict[str, Any]]
):
    found = None
    for plugin_file in client.plugins.files.get(plugin_id=plugin_id, page_length=100000)['data']:
        if plugin_file['filename'] == filename:
            found = plugin_file
    if (found != None):
        return client.plugins.files.modify_by_id(
            plugin_id=plugin_id,
            plugin_file_id=found['id'],
            filename=filename,
            contents=contents, 
            description=description, 
            tasks=tasks
        )
    else:
        return client.plugins.files.create(
            plugin_id=plugin_id, 
            filename=filename, 
            contents=contents, 
            description=description, 
            tasks=tasks
        )

def register_plugins(
    client: DioptraClient[dict[str, Any]], 
    group: int, 
    plugins_to_upload: dict[str, Any],
):
    plugins = []
    for plugin_file in plugins_to_upload.keys():
        plugin_path = Path(plugin_file)
        contents = plugin_path.read_text().replace("\r", '')
        tasks = plugins_to_upload[plugin_file]
        filename = plugin_path.name
        description = 'custom plugin for ' + filename
        plugin_id = create_or_get_plugin(client, group, plugin_path.parent.name, description)['id']
        plugins += [plugin_id]
        uploaded_file = create_or_modify_plugin_file(client, plugin_id, filename, contents, description, tasks)
    return list(set(plugins))

def create_parameters_object(params: dict[str, Any]):
    ret = []
    type_map = {'int': 'integer', 'float':'float', 'string':'string', 'list':'list', 'bool': 'boolean', 'dict': 'mapping'}
    for p in params:
        if (type(params[p]).__name__ in type_map.keys()):
            paramType = type_map[type(params[p]).__name__]
            defaultValue = str(params[p])
        else:
            defaultValue = str(params[p])
            paramType = 'string'
        
        param_obj = {
            'name': p,
            'defaultValue': str(defaultValue),
            'parameterType': paramType
        }
        
        ret += [param_obj]
    
    return ret

def get_graph_for_upload(yaml_text: list[str]):
    i = 0
    for line in yaml_text:
        if line.startswith("graph:"):
            break
        i += 1
    return ''.join(yaml_text[i+1:])

def register_entrypoint(
    client: DioptraClient[dict[str, Any]],
    name: str, 
    description: str, 
    queues: list[int], 
    plugins: list[int], 
    yaml_file: str
) -> dict[str, Any]:
    yaml = read_yaml(yaml_file)
    #task_graph = yaml['graph']
    parameters = yaml['parameters']
    
    with open(yaml_file, 'r') as f:
        lines = f.readlines()
    task_graph = get_graph_for_upload(lines).replace('\r','')
    
    entrypoint = create_or_get_entrypoints(client, 1, name, description, task_graph, create_parameters_object(parameters), queues, plugins)
    return entrypoint

def add_missing_plugin_files(location: str, upload: dict[str, Any]):
    p = Path(location)
    for child in p.iterdir():
        if (child.name.endswith('.py')):
            if (str(child) not in upload.keys()):
                upload[str(child)] = []
    return upload

def upload_experiment(
    client: DioptraClient[dict[str, Any]], 
    entrypoint_filename: str, 
    entrypoint_name: str, 
    entrypoint_desc: str, 
    plugin_files: str, 
    queue_name: str, 
    queue_desc: str, 
    experiment_name: str, 
    experiment_desc: str
) -> tuple[int, int, int]:
    upload = get_plugins_to_register(client, entrypoint_filename, {})
    upload = add_missing_plugin_files(plugin_files, upload)
    queue = create_or_get_queue(client, 1, queue_name, queue_desc)
    queues = [queue['id']]
    plugins = register_plugins(client, 1, upload)
    entrypoint = register_entrypoint(client, entrypoint_name, entrypoint_desc, queues, plugins, entrypoint_filename)
    experiment = create_or_get_experiment(client, 1, experiment_name, experiment_desc, [entrypoint['id']])
    return experiment['id'], entrypoint['id'], queue['id']
  
def run_experiment(
    client: DioptraClient[dict[str, Any]],
    experiment_id: int, 
    job_desc: str, 
    queue_id: int, 
    entrypoint_id: int, 
    job_time_limit: str, 
    parameters = {}
) -> dict[str, Any]:
    return client.experiments.jobs.create(
        experiment_id=experiment_id,
        entrypoint_id=entrypoint_id,
        queue_id=queue_id,
        description=job_desc,
        values=parameters,
        timeout=job_time_limit
    )

def delete_all(client: DioptraClient[dict[str, Any]]):
    for d in client.experiments.get(page_length=100000)['data']:
        client.experiments.delete_by_id(d['id'])

    for d in client.entrypoints.get(page_length=100000)['data']:
        client.entrypoints.delete_by_id(d['id'])

    for d in client.jobs.get(page_length=100000)['data']:
        try:
          client.jobs.delete_by_id(d['id'])
        except:
          pass

    for d in client.models.get(page_length=100000)['data']:
        client.models.delete_by_id(d['id'])

    for d in client.plugins.get(page_length=100000)['data']:
        try:
            client.plugins.delete_by_id(d['id'])
        except:
            pass

    for d in client.tags.get(page_length=100000)['data']:
        client.tags.delete_by_id(d['id'])

    for d in client.plugin_parameter_types.get(page_length=100000)['data']:
        try:
            client.plugin_parameter_types.delete_by_id(d['id'])
        except:
            pass

    for d in client.queues.get(page_length=100000)['data']:
        client.queues.delete_by_id(d['id'])