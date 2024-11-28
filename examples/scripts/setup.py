import yaml
from pathlib import Path

basic_types = ['integer', 'string', 'number', 'any', 'boolean', 'null']

def create_or_get_experiment(client, group, name, description, entrypoints):
    found = None
    for exp in client.experiments.get_all(search=name,pageLength=100000)['data']:
        if exp['name'] == name:
            found = exp
    if (found != None):
        client.experiments.add_entrypoints_by_experiment_id(found['id'], entrypoints)
        return found
    else:
        return client.experiments.create(group, name, description, entrypoints)
def create_or_get_entrypoints(client, group, name, description, taskGraph, parameters, queues, plugins):
    found = None
    for entrypoint in client.entrypoints.get_all(search=name,pageLength=100000)['data']:
        if entrypoint['name'] == name:
            found = entrypoint
    if (found != None):
        client.entrypoints.modify_by_id(found['id'], name, description, taskGraph, parameters, queues)
        client.entrypoints.add_plugins_by_entrypoint_id(found['id'], plugins)
        return found
    else:
        return client.entrypoints.create(group, name, description, taskGraph, parameters, queues, plugins)
def create_or_get_plugin_type(client, group, name, description, structure):
    ret = None
    for pt in client.pluginParameterTypes.get_all(pageLength=100000)['data']:
        if (pt['name'] == name):
            ret = pt
    if (ret is None):
        ret = client.pluginParameterTypes.create(group, name, description, structure)
    return ret
def find_plugin_type(client, name, types):
    for t in types.keys():
        if t == name:
            return create_or_get_plugin_type(client, 1, name, name, types[t])['id']
    for t in basic_types:
        if t == name:
            return create_or_get_plugin_type(client, 1, name, 'primitive', {})['id']

    print("Couldn't find type", name, "in types definition.")

def create_or_get_queue(client, group, name, description):
    ret = None
    for queue in client.queues.get_all(pageLength=100000)['data']:
        if queue['name'] == name:
            ret = queue
    if (ret is None):
        ret = client.queues.create(group, name, description)
    return ret
def plugin_to_py(plugin):
    return '../task-plugins/' + '/'.join(plugin.split('.')[:-1]) + '.py'
def create_inputParam_object(client, inputs, types):
    ret = []
    for inp in inputs:
        if 'name' in inp:
            inp_name = inp['name']
            inp_type = inp['type']
        else:
            inp_name = list(inp.keys())[0]
            inp_type = inp[inp_name]
        if 'required' in inp:
            inp_req = inp['required']
        else:
            inp_req = True
        inp_type = find_plugin_type(client, inp_type, types)
        ret += [{
           'name': inp_name,
           'parameterType': inp_type,
           'required': inp_req
        }]
    return ret
def create_outputParam_object(client, outputs, types):
    ret = []
    for outp in outputs:
        if isinstance(outp, dict):
            outp_name = list(outp.keys())[0]
            outp_type = outp[outp_name]
        else:
            outp_name = outp
            outp_type = outputs[outp_name]
        outp_type = find_plugin_type(client, outp_type, types)
        ret += [{
           'name': outp_name,
           'parameterType': outp_type,
        }]
    return ret

def read_yaml(filename):
    with open(filename) as stream:
        try:
            ret = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return ret
def register_basic_types(client, declared):
    for q in basic_types:
        type_def = create_or_get_plugin_type(client, 1, q, 'primitive', {})
    for q in declared:
        type_def = create_or_get_plugin_type(client, 1, q, 'declared', declared[q])
def get_plugins_to_register(client, yaml_file, plugins_to_upload=None):
    plugins_to_upload = {} if plugins_to_upload is None else plugins_to_upload
    yaml = read_yaml(yaml_file)
    task_graph = yaml['graph']
    plugins = yaml['tasks']
    types = yaml['types']
    
    register_basic_types(client, types)
    tasks = []
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
def create_or_get_plugin(client, group, name, description):
    ret = None
    for plugin in client.plugins.get_all(search=name,pageLength=100000)['data']:
        if plugin['name'] == name:
            ret = plugin
    if (ret is None):
        ret = client.plugins.create(group, name, description)
    return ret
def create_or_modify_plugin_file(client, plugin_id, filename, contents, description, tasks):
    found = None
    for plugin_file in client.plugins.files.get_files_by_plugin_id(plugin_id, pageLength=100000)['data']:
        if plugin_file['filename'] == filename:
            found = plugin_file
    if (found != None):
        return client.plugins.files.modify_files_by_plugin_id_file_id(plugin_id, found['id'], filename, contents, description, tasks)
    else:
        return client.plugins.files.create_files_by_plugin_id(plugin_id, filename, contents, description, tasks)
def register_plugins(client, group, plugins_to_upload):
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
def create_parameters_object(client, params):
    ret = []
    type_map = {'int': 'integer', 'float':'float', 'string':'string', 'list':'list', 'bool': 'boolean', 'dict': 'mapping'}
    for p in params:
        if (type(params[p]).__name__ in type_map.keys()):
            paramType = type_map[type(params[p]).__name__]
            #paramType='string' # TODO: remove if backend can handle types correctly
            defaultValue = str(params[p])
        else:
            defaultValue = str(params[p])
            paramType = 'string'
        name = p
        param_obj = {
            'name': name,
            'defaultValue': str(defaultValue),
            'parameterType': paramType
        }
        ret += [param_obj]
    return ret
def get_graph_for_upload(yaml_text):
    i = 0
    for line in yaml_text:
        if line.startswith("graph:"):
            break
        i += 1
    return ''.join(yaml_text[i+1:])
def get_parameters_for_upload(yaml_text):
    i = 0
    for line in yaml_text:
        if line.startswith("parameters:"):
            start = i
        if line.startswith("tasks:"):
            break
        i += 1
    return yaml_text[start:i+1]
def register_entrypoint(client, group, name, description, queues, plugins, yaml_file):
    yaml = read_yaml(yaml_file)
    #task_graph = yaml['graph']
    parameters = yaml['parameters']
    
    with open(yaml_file, 'r') as f:
        lines = f.readlines()
    task_graph = get_graph_for_upload(lines).replace('\r','')
    
    entrypoint = create_or_get_entrypoints(client, 1, name, description, task_graph, create_parameters_object(client, parameters), queues, plugins)
    return entrypoint
def add_missing_plugin_files(location, upload):
    p = Path(location)
    for child in p.iterdir():
        if (child.name.endswith('.py')):
            if (str(child) not in upload.keys()):
                upload[str(child)] = []
    return upload

def upload_experiment(client, entrypoint, entrypoint_name, entrypoint_desc, plugin_files, queue_name, queue_desc, experiment_name, experiment_desc):
    upload = get_plugins_to_register(client, entrypoint, {})
    upload = add_missing_plugin_files(plugin_files, upload)
    queue = create_or_get_queue(client, 1, queue_name, queue_desc)
    queues = [queue['id']]
    plugins = register_plugins(client, 1,upload)
    entrypoint = register_entrypoint(client, 1, entrypoint_name, entrypoint_desc, queues, plugins, entrypoint)
    experiment = create_or_get_experiment(client, 1, experiment_name, experiment_desc, [entrypoint['id']])
    return experiment['id'], entrypoint['id'], queue['id']
  
def run_experiment(client, experiment_id, job_desc, queue_id, entrypoint_id, job_time_limit, parameters = {}):
    return client.experiments.create_jobs_by_experiment_id(experiment_id, job_desc, queue_id, entrypoint_id, parameters, job_time_limit)

def delete_all(client):
    for d in client.experiments.get_all(pageLength=100000)['data']:
        client.experiments.delete_by_id(d['id'])
    for d in client.entrypoints.get_all(pageLength=100000)['data']:
        client.entrypoints.delete_by_id(d['id'])
    for d in client.jobs.get_all(pageLength=100000)['data']:
        try:
          client.jobs.delete_by_id(d['id'])
        except:
          pass
    for d in client.models.get_all(pageLength=100000)['data']:
        client.models.delete_by_id(d['id'])
    for d in client.plugins.get_all(pageLength=100000)['data']:
        try:
            client.plugins.delete_by_id(d['id'])
        except:
            pass
    for d in client.tags.get_all(pageLength=100000)['data']:
        client.tags.delete_by_id(d['id'])
    for d in client.pluginParameterTypes.get_all(pageLength=100000)['data']:
        try:
            client.pluginParameterTypes.delete_by_id(d['id'])
        except:
            pass
    for d in client.queues.get_all(pageLength=100000)['data']:
        client.queues.delete_by_id(d['id'])