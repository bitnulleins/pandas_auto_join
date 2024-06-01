import traceback
import logging
import pandas as pd
import numpy as np

from pandas_auto_join import config
from difflib import SequenceMatcher
from Levenshtein import ratio, jaro, jaro_winkler, seqratio, setratio, matching_blocks, editops
from typing import Tuple
from tqdm import tqdm

__version__ = "1.0.0"

def join(
    *args: Tuple[pd.DataFrame], 
    how: str = 'inner',
    strategy: str = 'levenshtein',
    threshold: float = 0.5,
    verbose: int = 0
) -> pd.DataFrame:
    """Main method for joining two or more dataframes into one.

    Parameters
    ----------
    *args : Tuple[pd.DataFrame]
        A tuple of input dataframes
    how : str, optional
        Join type, by default 'left'
    strategy : str, optional
        Similarity algorithm: jaro, levenshtein (default)
    threshold: float, optional
        Threshold for similarity between 0.0 (no similarity check) and 1.0 (equi-join)
    verbose : int, optional
        Show running comments, by default 0

    Returns
    -------
    pd.DataFrame
        Finished new final joined dataframe
    """
    try:
        if similarity_threshold < 0 or similarity_threshold > 1:
            raise Exception("Similarity float value threshold has to be between 0 and 1.")
        config.setting['VERBOSE'] = verbose
        if len([df for df in args if isinstance(df, pd.DataFrame)]):
            for idx, df in tqdm(enumerate(args), desc='[INFO] JOIN DATAFRAMES', total=len(args), unit='df', leave=config.setting['VERBOSE']):
                df.index.name = f"df{idx}"
                if idx == 0:
                    main_df = df.drop_duplicates()
                    begin_columns = main_df.columns
                    if len(args) > 1: continue
                    else: return main_df
                
                other_df = df.drop_duplicates()

                # Find number join keys
                main_df, other_df = __extract_dtypes(
                    df1         = main_df.copy(),
                    df2         = other_df.copy()    
                )

                # Find (similarity) string join keys
                main_df, other_df = __generate_similarity(
                    df1         = main_df.copy(),
                    df2         = other_df.copy(),
                    algo        = similarity_strategy,
                    threshold   = similarity_threshold
                )

                # Find overlap possible keys
                left_key, right_key = __join_keys(
                    df1         = main_df.copy(),
                    df2         = other_df.copy()
                )

                # Merge other_df to main_df
                index_name = main_df.index.name
                main_df = pd.merge(
                    left        = main_df.dropna(subset=left_key),
                    right       = other_df.dropna(subset=right_key),
                    left_on     = left_key,
                    right_on    = right_key,
                    how         = how,
                    suffixes    = ('','_duplicated')
                )
                main_df.index.name = index_name
                main_df = main_df.loc[:,~main_df.columns.str.startswith(config.setting['JOIN_PREFIX'])]

                if config.setting['VERBOSE']: logging.info(f"Added {len(other_df[right_key].dropna())} new data rows to dataframe.")

            new_columns = list(set(begin_columns) ^ set(main_df.columns))
            if len(new_columns) > 0:
                if config.setting['VERBOSE']: logging.info(f"Finished. Added {len(new_columns)} new columns to final dataframe: {', '.join(new_columns)}")
            else:
                if config.setting['VERBOSE']: logging.warning("Finished, but add no new columns!")

            return main_df
        else:
            logging.error("Required at least one valid Pandas DataFrame!")
    except Exception as e:
        if config.setting['DEBUG']: print(traceback.format_exc())
        logging.error(f"Some error occurred: {e}") 

def __extract_dtypes(
            df1: pd.DataFrame,
            df2: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Extract date and number as primitive datatypes for given dataframes.

    Parameters
    ----------
    df1 : pd.DataFrame
        First dataframe
    df2 : pd.DataFrame
        Second dataframe

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        Two dataframes with extracted number and datetypes as new column
    """
    def convert_dtypes(df: pd.DataFrame) -> pd.DataFrame:
        """Converts each column to its data type (dtype)."""
        today = pd.to_datetime('today').date()
        
        for column in df.select_dtypes(include='number').columns:
            df[__column_name(df, column)] = pd.to_numeric(df[column].replace('.','').replace(',','.'), downcast='float', errors='coerce')

        for column in df.select_dtypes(include='object', exclude='number').columns:
            dates = pd.to_datetime(df[column], errors='coerce')

            if not dates.isna().any():
                if (dates.dt.date == today).all():
                    df[__column_name(df, column)] = pd.NaT
                else:
                    df[__column_name(df, column)] = dates

        return df
    
    df1 = convert_dtypes(df1).dropna(axis=1,how='all')
    df2 = convert_dtypes(df2).dropna(axis=1,how='all')

    return df1, df2

def __generate_similarity(
            df1: pd.DataFrame,
            df2: pd.DataFrame,
            algo: str,
            threshold: float
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generates similar text matches for all text columns for given dataframes.

    Parameters
    ----------
    df1 : pd.DataFrame
        First dataframe
    df2 : pd.DataFrame
        Second dataframe
    algo : str
        Similarity algorithm
    threshold : float
        Cutoff threshold for similarity

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        Dataframe with similar text matches
    """
    def clean_regex() -> str:
        """Regular expression (regex) for removing unnecessary symbols."""
        return '[\;\(\)\[\]\"\']+'

    def preprocessing(x: object) -> str:
        """String preparation before similarity matching."""
        return str(x).upper().strip()
    
    def calc_similarity(str1, str2):
        """Return similarity between two strings for different algorithm.""" 
        if algo == 'jaro':
            score = jaro(str1, str2)
        else:
            # Levensthein
            score = ratio(str1, str2)
        
        return score

    def best_match(str1, series, first):
        sim_score = series.apply(lambda y: calc_similarity(str1,y))
        max_sim = sim_score.max()

        str2 = series[sim_score.idxmax()]
        # Generate equal matching string (switch between df 0 and 1)
        if first:
            mb = matching_blocks(editops(str1,str2), str1, str2)
            match_str = ''.join([str1[x[0]:x[0]+x[2]] for x in mb])
        else:
            mb = matching_blocks(editops(str2,str1), str2, str1)
            match_str = ''.join([str2[x[0]:x[0]+x[2]] for x in mb])

        return match_str if max_sim >= threshold else None

    col1 = df1.loc[:, df1.columns.str.startswith(config.setting['JOIN_PREFIX'])].columns
    col2 = df2.loc[:, df2.columns.str.startswith(config.setting['JOIN_PREFIX'])].columns
    col1 = df1.drop(columns=col1).drop(columns=col1.str.replace(__column_name(df1,''),'')).columns
    col2 = df2.drop(columns=col2).drop(columns=col2.str.replace(__column_name(df2,''),'')).columns
    combinations = np.array(np.meshgrid(col1, col2)).T.reshape(-1, 2)

    for combination in combinations:
        series1 = df1[combination[0]].replace(clean_regex(), ' ', regex=True).replace('\s+',' ', regex=True).apply(preprocessing)
        series2 = df2[combination[1]].replace(clean_regex(), ' ', regex=True).replace('\s+',' ', regex=True).apply(preprocessing)

        df1[__column_name(df1, f"{combination[0]}<->{combination[1]}")] = series1.apply(lambda x: best_match(x, series2, True))
        df2[__column_name(df2, f"{combination[0]}<->{combination[1]}")] = series2.apply(lambda x: best_match(x, series1, False))

    return df1.dropna(axis=1,how='all'), df2.dropna(axis=1,how='all')

def __join_keys(
            df1: pd.DataFrame,
            df2: pd.DataFrame
    ) -> Tuple[list, list]:
    """Possible join keys are derived in this method.
    Lengths and data types are compared for this purpose.
    The columns with the same lengths and data types are assumed to be possible keys.

    Parameters
    ----------
    df1 : pd.DataFrame
        Main (left) dataframe for join.
    df2 : pd.DataFrame
        To join dataframe (left)

    Returns
    -------
    Tuple[list, list]
        Two lists for possible join keys (left and right)

    Raises
    ------
    Exception
        Didnt find any possible join key
    """
    col1 = df1.loc[:, df1.columns.str.startswith(config.setting['JOIN_PREFIX'])].columns
    col2 = df2.loc[:, df2.columns.str.startswith(config.setting['JOIN_PREFIX'])].columns
    combinations = np.array(np.meshgrid(col1, col2)).T.reshape(-1, 2)

    intersection_len = {}
    for combination in combinations:
        series1 = df1[combination[0]].dropna()
        series2 = df2[combination[1]].dropna()

        # Only check same dtype oder str, where column name is equal!
        str_type = series1.dtype == 'object' and series2.dtype == 'object'
        same_col = combination[0].replace(__column_name(df1),'') == combination[1].replace(__column_name(df2),'')
        same_type = series1.dtype == series2.dtype
        if not ((str_type and same_col) or (same_type and not str_type)): continue

        set1 = set(series1)
        set2 = set(series2)
        
        if min(len(set1),len(set2)) == 0: intersecion_score = 0
        else: intersecion_score = len(set1.intersection(set2)) / min(len(set1), len(set2))

        intersection_len[tuple(combination)] = round(intersecion_score * min(len(series1.dropna()),len(series2.dropna())))

    sorted_intersection = sorted(intersection_len.items(), key=lambda item: item[1], reverse=True)
    max_overlap = 0 if len(sorted_intersection) == 0 else max([item for item in intersection_len.values()])
    possible = {k: v for k, v in sorted_intersection if v >= max_overlap}
    if len(possible) == 0: raise Exception("No possible join keys found.")

    left_key, right_key = zip(*possible)
    # Check if column combination are unique, otherwise remove similar key
    max_length = min(len(set(left_key)), len(set(right_key)))
    left_key, right_key = list(left_key)[:max_length], list(right_key)[:max_length]

    if config.setting['VERBOSE']:
        logging.info(f"Max quantity similarity: {max_overlap}")
        lst_left_keys   = ', '.join(left_key).replace(config.setting['JOIN_PREFIX'],'')
        lst_right_keys  = ', '.join(right_key).replace(config.setting['JOIN_PREFIX'],'')
        logging.info(f"Join by [{lst_left_keys}] <-> [{lst_right_keys}]")
    
    return left_key, right_key

def __column_name(df: pd.DataFrame, columns = '') -> str:
    """Return unique name for each dataframe with global prefix.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe where name from
    columns : _type_
        Specific column name

    Returns
    -------
    str
        Unique name for column
    """
    return f"{config.setting['JOIN_PREFIX']}{df.index.name}_{columns}"