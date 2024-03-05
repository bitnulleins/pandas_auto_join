import traceback
import logging
import pandas as pd
import numpy as np
import math
import config

from typing import Tuple
from tqdm import tqdm

"""
A tool to perform an automatic join of Pandas DataFrames.
A possible primary and foreign key is automatically found.
"""

def join(
    *args: Tuple[pd.DataFrame], 
    how: str = 'inner',
    verbose: int = 0
) -> pd.DataFrame:
    """Main method for joining two or more dataframes into one.

    Parameters
    ----------
    *args : Tuple[pd.DataFrame]
        A tuple of input dataframes
    how : str, optional
        Join type, by default 'left'
    intersection: float, optional
        Threshold 0.0 to 1.0 how much values should intersect
    verbose : int, optional
        Show running comments, by default 0

    Returns
    -------
    pd.DataFrame
        Finished new final joined dataframe
    """
    try:
        if verbose: logging.info(f"Used unique join prefix: {config.setting['UUID']}")
        if len([df for df in args if isinstance(df, pd.DataFrame)]):
            for idx, df in tqdm(enumerate(args), desc='[INFO] JOIN DATAFRAMES', total=len(args), unit='df'):
                if df.index.name == None: df.index.name = f"DF{idx}"

                if len(df.columns) == 1:
                    raise Exception(f"Dataframe {df.index.name} has only one column. Nothing to join.")

                # Prepare dataframe
                if idx == 0:
                    start_columns = df.columns
                    start_rows = len(df)
                    main_df     = __prepare(df, verbose)
                    main_df_copy= main_df.copy()
                    # Stop if first (main) df preparation is finished
                    if len(args) > 1: continue
                    else: return main_df
                else:
                    other_df    = __prepare(df, verbose)

                # Find and prepare possible join key
                left_key, right_key     = __join_key(main_df_copy, other_df, start_columns, verbose)
                main_df, left_key_tmp   = __prepare_join_key(main_df, left_key)
                other_df, right_key_tmp = __prepare_join_key(other_df, right_key)
                
                # Merge other_df to main_df
                main_df = pd.merge(
                    left        = main_df,
                    right       = other_df,
                    left_on     = left_key_tmp,
                    right_on    = right_key_tmp,
                    how         = how,
                    suffixes    = (None,'_joined')
                )

                # Reset index name after merge
                main_df.index.name = main_df_copy.index.name

                if verbose: logging.info(f"{other_df.index.name} | Sucessfully added {len(main_df[right_key].dropna())} new data rows.")
                main_df.drop(columns=right_key + right_key_tmp, inplace=True)

            # Clean output
            tmp_columns_regex = fr'^(?!{config.setting["UUID"]}_).+'
            main_df = main_df.filter(regex=tmp_columns_regex, axis=1)

            new_columns = list(set(start_columns) ^ set(main_df.columns))
            if len(new_columns) > 0:
                logging.info(f"Finished. Added {len(new_columns)} new columns to final dataframe: {', '.join(new_columns)}")
            else:
                logging.warning("Finished, but add no new columns!")

            if how == 'inner':
                removed_rows = len(main_df) - start_rows
                logging.warning(f"INNER-JOIN removes {removed_rows} rows ({round(removed_rows/start_rows*100,1)}%) in final dataframe.")

            return main_df
        else:
            logging.error("Required at least one valid Pandas DataFrame!")
    except Exception as e:
        if config.setting['DEBUG']: print(traceback.format_exc())
        logging.error(f"Some error occurred: {e}")

def __prepare(df: pd.DataFrame, verbose: int) -> pd.DataFrame:
    """Prepares the dataframe for joining. The following is done:
    - Derive data types automatically
    - Downcast numeric dtypes all to float, for best length match

    Parameters
    ----------
    df : pd.DataFrame
        Unprepared input dataframe
    verbose : int
        Show running comments

    Returns
    -------
    pd.DataFrame
        Prepared dataframe
    """

    def convert_dtypes(df: pd.DataFrame) -> pd.DataFrame:
        """Converts each column to its data type (dtype)."""
        for column in df.columns:
            df[column] = pd.to_numeric(df[column], downcast='float', errors='ignore')

        for column in df.select_dtypes(include='object', exclude='number').columns:
            df[column] = pd.to_datetime(df[column], errors='ignore')

        for column in df.select_dtypes(include='datetime', exclude=['number','object']).columns:
            df[column] = df[column].fillna(pd.NaT)
            
        return df
    
    df = convert_dtypes(df)

    num_col = len(df.select_dtypes('number').columns)
    date_col = len(df.select_dtypes('datetime').columns)
    str_col = len(df.select_dtypes('object').columns)

    if verbose: logging.info(f"{df.index.name} | Dataframe has {num_col} numeric, {date_col} datetime and {str_col} text columns.")
    return df

def __join_key( main_df: pd.DataFrame,
                other_df: pd.DataFrame,
                columns: list,
                verbose: int
    ) -> Tuple[list, list]:
    """Possible join keys are derived in this method.
    Lengths and data types are compared for this purpose.
    The columns with the same lengths and data types are assumed to be possible keys.

    Parameters
    ----------
    main_df : pd.DataFrame
        Main (left) dataframe for join.
    other_df : pd.DataFrame
        To join dataframe (left)
    columns : list
        Column list of beginner dataframe
    verbose : int
        Show running comments

    Returns
    -------
    Tuple[list, list]
        Two lists for possible join keys (left and right)

    Raises
    ------
    Exception
        Didnt find any possible join key!
    """
    def non_empty(series1, series2):
        return series1.empty or series2.empty

    def check_length(series1, series2):
        return series1.astype(str).replace('\s+','').str.len().mode()[0] != series2.astype(str).replace('\s+','').str.len().mode()[0]
    
    def check_dtype(series1, series2):
        return series1.dtype != series2.dtype

    combinations = np.array(np.meshgrid(columns, other_df.columns)).T.reshape(-1, 2)
    intersection_len = {}
    for combination in combinations:
        series1 = main_df[combination[0]].dropna()
        series2 = other_df[combination[1]].dropna()

        if non_empty(series1, series2): continue
        if check_length(series1, series2): continue
        if check_dtype(series1, series2): continue
        
        set1 = set(main_df[combination[0]])
        set2 = set(other_df[combination[1]])
        intersection = set1.intersection(set2)
        intersection_len[tuple(combination)] = len(intersection) / max(len(main_df), len(other_df))

    # Find best intersection
    sorted_intersection = sorted(intersection_len.items(), key=lambda item: item[1], reverse=True)
    intersection_threshold = math.floor((len(other_df) / max(len(main_df), len(other_df))) * 10) / 10
    possible = {k: v for k, v in sorted_intersection if v >= intersection_threshold}
    if len(possible) == 0: raise Exception("No possible join-key found!")
    left_key, right_key = zip(*possible)

    # Check if column combination are unique, otherwise remove similar key
    max_length = min(len(set(left_key)), len(set(right_key)))
    left_key, right_key = list(left_key)[:max_length], list(right_key)[:max_length]

    if verbose:
        logging.info(f"{other_df.index.name} | Dynamically calculated threshold: {intersection_threshold}")
        logging.info(f"{other_df.index.name} | Join by {main_df.index.name}[{', '.join(left_key)}] <-> {other_df.index.name}[{', '.join(right_key)}]")
    return left_key, right_key

def __prepare_join_key(df: pd.DataFrame, keys: list) -> pd.DataFrame:
    """Temporary join columns are created that have been transformed to increase the chance of a successful join.

    Parameters
    ----------
    df : pd.DataFrame
        Transformable dataframe
    keys : list
        Join keys that has to transform

    Returns
    -------
    pd.DataFrame
        Dataframe with prepared temporary join columns
    """
    # Remove whitespaces, clean values for for possible misspellings
    tmp_keys = []
    for key in keys:
        tmp_column = f'{config.setting["UUID"]}_{key}'
        tmp_keys.append(tmp_column)
        df[tmp_column] = df[key].replace('\s+', '', regex=True)

    return df, tmp_keys