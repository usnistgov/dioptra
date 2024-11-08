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

"""Functions to download data into a directory for demo.ipynb"""


import os
import re
import urllib
from urllib.request import urlretrieve

import aif360
import pandas as pd
from aif360.datasets import AdultDataset, CompasDataset
from folktables import (
    ACSDataSource,
    ACSEmployment,
    ACSHealthInsurance,
    ACSIncome,
    generate_categories,
    load_definitions,
)


# function to check if raw data is downloaded already
def check_data_or_download(destn, files, data_source_directory):
    """Helper function to download datasets for aif360 module"""

    check = all(item in os.listdir(destn) for item in files)
    if check:
        print("All files in {files} have already been downloaded.")
    else:
        print("Some files are missing. Downloading now.")
        for data_file in files:
            _ = urllib.request.urlretrieve(
                data_source_directory + data_file, os.path.join(destn, data_file)
            )


def get_compas_dataset(dir="data"):
    """Get the prison recidvism classification dataset from aif360 module"""

    save_path = os.path.join(dir, "compas_data.csv")

    if not os.path.isfile(save_path):

        LIB_PATH = aif360.__file__.rsplit("aif360", 1)[0]
        data_source_directory = "https://raw.githubusercontent.com/propublica/compas-analysis/refs/heads/master/"
        destn = os.path.join(LIB_PATH, "aif360", "data", "raw", "compas")
        files = ["compas-scores-two-years.csv"]
        check_data_or_download(destn, files, data_source_directory)

        compas_dataset = CompasDataset()
        df, meta_data = compas_dataset.convert_to_dataframe()
        df.to_csv(save_path, index=False)

    else:
        compas_dataset = CompasDataset()
        df, meta_data = compas_dataset.convert_to_dataframe()

    return df, meta_data


def get_income_dataset(dir="data"):
    """Get the income classification dataset (census data) from aif360 module"""

    save_path = os.path.join(dir, "census_data.csv")

    if not os.path.isfile(save_path):

        LIB_PATH = aif360.__file__.rsplit("aif360", 1)[0]
        data_source_directory = (
            "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/"
        )
        destn = os.path.join(LIB_PATH, "aif360", "data", "raw", "adult")
        files = ["adult.data", "adult.test", "adult.names"]
        check_data_or_download(destn, files, data_source_directory)

        census_dataset = AdultDataset()

        df, meta_data = census_dataset.convert_to_dataframe()

        df["income_below_50K"] = df["income-per-year"].apply(
            lambda x: 1.0 if x == 0 else 0.0
        )
        df = df.drop("income-per-year", axis=1)
        df.to_csv(save_path, index=False)

    else:
        compas_dataset = AdultDataset()
        df, meta_data = compas_dataset.convert_to_dataframe()

    return df, meta_data


def get_wine_quality_dataset(dir="data"):
    """Download regression example dataset of wine quality scores"""

    wine_data_url = "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv"
    save_path = os.path.join(dir, "wine_data.csv")

    if not os.path.isfile(save_path):
        urlretrieve(wine_data_url, save_path)

        # Convert semicolons to commas to make CSV
        with open(save_path, "r") as file:
            data = file.read().replace(";", ",")

        with open(save_path, "w") as file:
            file.write(data)

    df = pd.read_csv(save_path)
    return df


# def get_ACS_PUMS_col_names_to_labels():
#     """Helper function to clean column names for ACS data"""
#
#     def clean_name(text):
#         text = re.sub(r'\(.*?\)','', text)
#         text = re.sub(' ', '_', text)
#         text = re.sub(r'[^A-Za-z0-9_]+', '', text)
#
#         return text
#
#     url = 'https://api.census.gov/data/2018/acs/acs1/pums/variables.html'
#     tables = pd.read_html(url)
#     table_df = tables[0][['Name', 'Label']]
#     table_df.loc[:, 'Label'] = table_df['Label'].apply(clean_name)
#     name_to_label = dict(zip(table_df['Name'], table_df['Label']))
#
#     return name_to_label
#
#
# def get_ACS_insurance_dataset(remake =False, year = '2018', horizon = '1-Year', dir='data', states=['CA']):
#     """Download arbitrary ACS data from folktables module"""
#
#     os.makedirs(dir, exist_ok=True)
#     data_path = os.path.join(dir, 'ACS_insurance_dataset.csv')
#
#     # Create ACS IPUMS tabular dataset of person level vars and insurance coverage outcome var
#     # Uses folktables package for reproducible ML with census data
#
#     if not os.path.isfile( data_path) or remake:
#
#         data_source = ACSDataSource(survey_year=year, horizon=horizon, survey='person')
#
#         acs_data_no_dummies = data_source.get_data(states=states, download=True)
#
#         features, _, __ = ACSHealthInsurance.df_to_pandas(acs_data_no_dummies)
#
#         # Get definitions for categorical variables coded as integers
#         defin_df = data_source.get_definitions(True)
#         categories = generate_categories(features=features, definition_df=defin_df)
#
#         # Get labels for column names to make more intuitive
#         name_to_label = get_ACS_PUMS_col_names_to_labels()
#
#         features_labeled, labels, _ = ACSHealthInsurance.df_to_pandas(acs_data_no_dummies, categories=categories, dummies=False)
#
#         features_labeled.rename(columns= name_to_label, inplace=True)
#         labels.rename(columns = name_to_label, inplace=True)
#
#
#         features_turn_to_nan = features_labeled.apply(pd.to_numeric, errors='coerce')
#
#         numeric_df = features_turn_to_nan.dropna(axis=1, how='all')
#         non_numeric_df = features_labeled[features_labeled.columns.difference(numeric_df.columns,sort=False)]
#
#         non_numeric_dummies = pd.get_dummies(non_numeric_df, drop_first=True).astype(int)
#
#         features_dummies = pd.merge( numeric_df, non_numeric_dummies, left_index=True, right_index=True)
#
#         full_df = pd.merge( labels.astype(int), features_dummies, left_index=True, right_index=True)
#
#         full_df = full_df.dropna()
#         full_df.to_csv(data_path, index=False)
#
#         return full_df
#
#     else:
#         return pd.read_csv(data_path)
