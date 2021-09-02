# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode
import os
import shutil
from pathlib import Path
import boto3

import yaml

TARGET_FILES = set(["conda.yaml", "MLmodel", "keras_module.txt", "save_format.txt", "model.h5"])

def _find_s3_files(s3_resource, target_filenames):
    # Look through all bucket files, and place matching file objects with associated target file.
    target_s3_files = {target : [x for bucket in s3_resource.buckets.all() for x in bucket.objects.all() if target in x.key] for target in target_filenames}
    return target_s3_files


def _filter_h5_save_format_files(s3_resource, save_format_list, model_h5_list):
    address_list = []

    if (len(model_h5_list) == 0):
        return []
    bucket_name = model_h5_list[0].bucket_name

    # Extract list of all h5 model data directories.
    for model in model_h5_list:
        address_list.append(model.key.replace("/model.h5", ""))

    # Remove any save formats that do not correspond w/ h5 model dir.
    for save_format in save_format_list:
        save_format_dir = save_format.key.replace("/save_format.txt", "")
        if save_format_dir not in address_list:
            save_format_list.remove(save_format_dir)
        else:
            # Update h5 address list until only addresses left are those missing a save_format.txt
            address_list.remove(save_format_dir)

    # For any model.h5 directory that's missing a save_format.txt file, create a new empty S3 object and add to save_format list.
    for missing_file in address_list:
        new_save_format_file = s3_resource.Object(bucket_name, missing_file + "/save_format.txt")
        save_format_list.append(new_save_format_file)

    return save_format_list

def migrate_s3(s3_resource):
    s3_files = _find_s3_files(s3_resource, TARGET_FILES)
    s3_files["save_format.txt"] = _filter_h5_save_format_files(s3_resource,
                                                               s3_files["save_format.txt"],
                                                               s3_files["model.h5"])
    _update_s3_file_conda_yml(s3_files['conda.yaml'])
    _update_s3_file_save_format(s3_files['save_format.txt'])
    _update_s3_keras_module(s3_files['keras_module.txt'])
    _update_s3_mlmodel_yaml(s3_files['MLmodel'])


def _load_yaml_file_from_s3(s3_object):
    return yaml.safe_load(s3_object.get()['Body'].read().decode('utf-8'))


def _dump_yaml_file_into_s3(s3_object, yaml_file):
    s3_object.put(Body=yaml.dump(data=yaml_file, Dumper=yaml.Dumper))


def _load_txt_file_from_s3(s3_object):
    return s3_object.get()['Body'].read().decode('utf-8')


def _upload_txt_file_into_s3(s3_object, txt):
    s3_object.put(Body=txt)


def _update_s3_keras_module(keras_module_files):
    for s3_object in keras_module_files:
        file_txt = _load_txt_file_from_s3(s3_object)
        if not ("tensorflow.keras" in file_txt):
            file_txt = "tensorflow.keras"
            _upload_txt_file_into_s3(s3_object, file_txt)


def _update_s3_file_save_format(save_format_files):
    for s3_object in save_format_files:
        file_txt = "h5"
        _upload_txt_file_into_s3(s3_object, file_txt)


def _update_s3_mlmodel_yaml(mlmodel_yaml_files):
    for s3_object in mlmodel_yaml_files:
        mlmodel_yaml = _load_yaml_file_from_s3(s3_object)
        if "keras" in mlmodel_yaml["flavors"]:
            mlmodel_yaml["flavors"]["keras"]["keras_module"] = "tensorflow.keras"
            mlmodel_yaml["flavors"]["keras"]["keras_version"] = "2.4.0"
            mlmodel_yaml["flavors"]["python_function"]["python_version"] = "3.9"
            _dump_yaml_file_into_s3(s3_object, mlmodel_yaml)


def _update_s3_file_conda_yml(conda_yml_files):
    for s3_object in conda_yml_files:
        conda_yaml = _load_yaml_file_from_s3(s3_object)
        dependencies = conda_yaml["dependencies"]
        dependencies_new = []
        for dep in dependencies:
            if isinstance(dep, str) and "python" in dep:
                dependencies_new.append("python=3.9")

            elif isinstance(dep, dict):
                dependencies_new.append(
                    {
                        "pip": [
                            "tensorflow==2.4.1" if "tensorflow" in x else x
                            for x in dep["pip"]
                        ]
                    }
                )
            else:
                dependencies_new.append(dep)

        conda_yaml["dependencies"] = dependencies_new
        _dump_yaml_file_into_s3(s3_object, conda_yaml)

