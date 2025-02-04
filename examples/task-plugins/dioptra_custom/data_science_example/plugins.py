from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union, Any

import structlog
from structlog.stdlib import BoundLogger

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import os

from dioptra import pyplugs
from dioptra.client import connect_json_dioptra_client

import mlflow 

from .artifacts_mlflow import upload_data_frame_artifact, download_all_artifacts, extract_tarfile


LOGGER: BoundLogger = structlog.stdlib.get_logger()

@pyplugs.register
def gen_poly_func(
    poly_degree, 
    min_x = 0,
    max_x=100,
    y_range_max=100
    ) -> Dict[str, Any]:
    """
    Generates a polynomial function and associated metadata.

    This function creates a polynomial of degree `poly_degree` with roots between 
    `min_x` and `max_x`, and scales its range to fit within [-`y_range_max`, `y_range_max`].

    Args:
        poly_degree (int): The degree of the polynomial
        min_x (int, optional): The minimum value of x for the polynomial's roots. Defaults to 0.
        max_x (int, optional): The maximum value of x for the polynomial's roots. Defaults to 100.
        y_range_max (int, optional): The maximum absolute value of the polynomial's range. Defaults to 100.

    Returns:
        Dict[str, Any]: A dictionary containing the following keys:
            - 'poly_string' (str): A string representation of the polynomial.
            - 'poly_degree' (int): The degree of the polynomial.
            - 'min_x' (int): The minimum x value for the roots.
            - 'max_x' (int): The maximum x value for the roots.
            - 'y_range_max' (int): The maximum absolute value of the polynomial's range.
            - 'roots' (List[float]): The roots of the polynomial.
            - 'poly_function' (Callable[[Union[float, np.ndarray]], Union[float, np.ndarray]]): 
              The scaled polynomial function, which maps x values (single float or array) 
              to corresponding y values.
    """


    # Generate random roots between min_x and max_x
    random_roots = np.random.uniform(min_x, max_x, size=poly_degree)
    sorted_roots = np.sort(random_roots)  # Sort roots for spacing
    roots = [sorted_roots[0]]  # Start with the first root

    # Create min root spacing
    min_spacing = (max_x - min_x)/(poly_degree*4)
    
    # Adjust roots to ensure minimum spacing
    for root in sorted_roots[1:]:
        spaced_root = max(roots[-1] + min_spacing, root)
        roots.append(spaced_root)
        
    # Define a polynomial function based on these roots
    def polynomial(x):
        poly = 1
        for root in roots:
            poly *= (x - root)
        return poly
    
    # Generate x values between min_x and max_x
    x_values = np.linspace(min_x, max_x, 400)
    
    # Compute the corresponding y values
    y_values = polynomial(x_values)
    
    # Scale the polynomial by adjusting the coefficient to ensure y values stay between -y_range_max and y_range_max
    y_max = np.max(y_values)
    y_min = np.min(y_values)
    
    # Find the scale factor that limits y range to within [-y_range_max, y_range_max]
    scale_factor = y_range_max / max(abs(y_max), abs(y_min))
    
    # Adjust the polynomial function by applying the scale factor
    def scaled_polynomial(x):
        return scale_factor * polynomial(x)
    
    # Create string representation of polynomial
    terms = []
    for root in roots:
        if root == 0:
            terms.append(f"x")
        else:
            terms.append(f"(x - {root:.2f})")
    polynomial_str = f"f(x) = {scale_factor:.2f}" + "".join(terms)
    
    polynomial_dict = {
        'poly_string' : polynomial_str,
        'poly_degree' : poly_degree,
        'min_x' : min_x,
        'max_x' : max_x,
        'y_range_max': y_range_max,
        'roots' : roots,
        'poly_function': scaled_polynomial
    }

    return polynomial_dict


@pyplugs.register
def simulate_data_from_poly(
    polynomial_dict: Dict[str, Any], 
    sample_size ,
    noise_mean=0,
    noise_var=100
    ) -> pd.DataFrame:
    """
    Simulates data points based on a given polynomial function and adds Gaussian noise.

    This function uses a polynomial function defined in `polynomial_dict` to compute 
    true y-values for randomly sampled x-values within a specified range. Gaussian noise 
    is then added to the true y-values to simulate observed data.

    Args:
        polynomial_dict (Dict[str, any]): A dictionary containing information about the polynomial.
            This dict is generated in the plugin 'gen_poly_func'
        sample_size (int): The number of data points to simulate
        noise_mean (float, optional): The mean of the Gaussian noise added to y-values. Defaults to 0.
        noise_var (float, optional): The variance of the Gaussian noise added to y-values. Defaults to 100.

    Returns:
        pd.DataFrame: A DataFrame with two columns:
            - 'X' (float): The sampled x-values.
            - 'y' (float): The observed y-values, computed as the polynomial's true y-values plus noise.
    """

    # Unpack polynomial dict
    min_x, max_x = polynomial_dict['min_x'], polynomial_dict['max_x']
    poly_function = polynomial_dict['poly_function']

    # Sample data points between min_x and max_x
    X_sampled = np.random.uniform(min_x, max_x, sample_size)

    # Calculate the true y value based off the scaled polynomial
    y_true = poly_function(X_sampled)

    # Generate noise based on the given mean and variance
    noise = np.random.normal(loc=noise_mean, scale=np.sqrt(noise_var), size=sample_size)

    # Add noise to the true y values to get observed y
    y_observed = y_true + noise

    # Create a pandas DataFrame
    sim_data_df = pd.DataFrame({'X': X_sampled,'y': y_observed})

    return sim_data_df


@pyplugs.register
def upload_df(
        df : pd.DataFrame,
        file_name: str = 'uploaded_df.csv',
        file_format: str = 'csv'
)-> None:
    upload_data_frame_artifact(df, file_name, file_format, description = 'Simulated Data from polynomial')


def get_logged_in_session():
    url = "http://dioptra-deployment-restapi:5000/"
    dioptra_client = connect_json_dioptra_client(url)
    dioptra_client.auth.login(
        username=os.environ['DIOPTRA_WORKER_USERNAME'], 
        password=os.environ['DIOPTRA_WORKER_PASSWORD']
    )
    return dioptra_client


@pyplugs.register
def retrieve_first_artifact_by_job_id(experiment_id, job_id):
    """Hacky way to get saved df from MLFlow"""

    #client = connect_json_dioptra_client()
    #client.auth.login(
    #    username='dioptra-worker',
    #    password='Kjksa-Dbomaqqs-Uuiq-9'
    #    )
    
    client = get_logged_in_session()
    
    LOGGER.info(f"Experiment ID: {experiment_id}, Job ID: {job_id}")
    job_artifacts = client.experiments.jobs.get_by_id(experiment_id, job_id)['artifacts']
    df_uri = job_artifacts[0]['artifactUri']
    local_path = mlflow.artifacts.download_artifacts(artifact_uri=df_uri)
    df = pd.read_csv(local_path)
    
    LOGGER.info(df.head())

    return df

@pyplugs.register
def split_df(
    df: pd.DataFrame,
    estimator_degree: int,
    x_vars: List[str] | str = ['X'],
    y_var: str = 'y',
    OOD_percent = 20,
    test_size = .2

) -> Dict:
    
    """
    Perform polynomial expansion of the X variables, split the data into train, test, and out-of-distribution sets.
    
    Args:
        df (pd.DataFrame): Input DataFrame with X and y variables.
        x_vars (list): List of column names for X variables.
        y_var (str): Name of the target variable (y).
        estimator_degree (int): Degree of polynomial expansion (default=1).
        test_size (float): Proportion of the in-distribution data to include in the test split (default=0.2).
        OOD_percent (float): Percentage of data that isn't train/test that will be out of distribution (default 20%)
        
    Returns:
        out (dict): A dictionary containing train/test/OOD splits
    """
    

    if type(x_vars) is str:
        x_vars = [x_vars]
        
    # Extract the features (X) and target (y)
    X = df[x_vars]
    y = df[y_var]
    

    # Create polynomial features (without interaction terms)
    poly = PolynomialFeatures(degree=estimator_degree, include_bias=False)
    X_poly = poly.fit_transform(X)
    
    # Use the first variable in x_vars for percentile splitting
    x_first = X[x_vars[0]].values
    percentile = min(99, max(1, (100-OOD_percent)))
    percentile_val = np.percentile(x_first, percentile)
    
    # Split data into in-distribution and out-of-distribution based on the 80th percentile
    in_distribution_mask = x_first <= percentile_val
    out_of_distribution_mask = x_first > percentile_val
    
    # Get indices
    in_distribution_indices = np.where(in_distribution_mask)[0]
    out_of_distribution_indices = np.where(out_of_distribution_mask)[0]
    
    # Get in-distribution data
    X_in = X_poly[in_distribution_mask]
    y_in = y.values[in_distribution_mask]
    
    # Split in-distribution data into train and test randomly
    indices_in = in_distribution_indices
    X_train, X_test, y_train, y_test, train_idx, test_idx = train_test_split(
        X_in, y_in, indices_in, test_size=test_size, random_state=0)
    
    # Out-of-distribution data
    X_out = X_poly[out_of_distribution_mask]
    y_out = y.values[out_of_distribution_mask]
    out_of_distribution_idx = out_of_distribution_indices

    splits_dict = { 'X_train':X_train,
            'y_train' : y_train,
            'train_idx':train_idx,
            'X_test':X_test,
            'y_test' : y_test,
            'test_idx':test_idx,
            'X_out': X_out,
            'y_out': y_out,
            'out_of_distribution_idx' :out_of_distribution_idx}
    
    LOGGER.info('Successfully made splits')
    return splits_dict

@pyplugs.register
def fit_linear_model(splits_dict:Dict[str, Any]):

    X_train = splits_dict.get('X_train')
    y_train = splits_dict.get('y_train')
    
    # Fit a linear estimator (linear regression)
    model = LinearRegression()
    model.fit(X_train, y_train)

    return model


@pyplugs.register
def evaluate_linear_model(
    splits_dict: Dict[str, Any],
    model
) -> Dict[str, Any]:

    X_train, y_train = (splits_dict.get("X_train"), splits_dict.get("y_train"))
    X_test, y_test = (splits_dict.get("X_test"), splits_dict.get("y_test"))
    X_out, y_out = (splits_dict.get("X_out"), splits_dict.get("y_out"))

    # Predict on the train, test, and out-of-distribution sets
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    y_out_pred = model.predict(X_out)
    
    # Calculate the mean squared error for all sets
    mse_train = mean_squared_error(y_train, y_train_pred)
    mse_test = mean_squared_error(y_test, y_test_pred)
    mse_out_of_distribution = mean_squared_error(y_out, y_out_pred)

    # Prepare the results
    metrics = {
        'MSE_train': mse_train,
        'MSE_test': mse_test,
        'MSE_out_of_distribution': mse_out_of_distribution,
        'MSE_ratio_test_train': mse_test / mse_train if mse_train != 0 else np.inf,
        'MSE_ratio_out_train': mse_out_of_distribution / mse_train if mse_train != 0 else np.inf
    }

    for metric_name, metric_value in metrics.items():
        mlflow.log_metric(key=metric_name, value=metric_value)
        LOGGER.info(
            "Log metric to MLFlow Tracking server",
            metric_name=metric_name,
            metric_value=metric_value,
        )

    return metrics
