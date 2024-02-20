import logging
import click
import os
import pandas as pd

import pandas_auto_join as aj
from tqdm import tqdm

@click.command()
@click.argument('files', type=click.Path(exists=True), nargs=-1, required=True)
@click.option('--how', '-h', default='inner', show_default=True, type=click.Choice(['left', 'inner', 'outer'], case_sensitive=True), help="Pandas merge type.")
@click.option('--output', '-o', default=None, help="Name of output file with file extension.")
@click.option('--verbose', '-v', default=0, show_default=True, help="Print feedback while running.")
def main(files, how, output, verbose):
    """Command to load and auto join two or more dataframes.
    Actually support PARQUET and CSV files."""
    list_of_df = []
    try:
        for idx, file in tqdm(enumerate(files), desc='[INFO] READ DATAFRAMES', total=len(files), unit='df'):
            filename, ext = os.path.splitext(os.path.basename(file))

            # Save file extension for main file
            if idx == 0: first_file_ext = ext

            try:
                if ext in ['.parquet','.csv']:
                    if ext == '.parquet': 
                        df = pd.read_parquet(file)
                    elif ext == '.csv':
                        df = pd.read_csv(file, sep=',')
                        if df.shape[1] == 1: df = pd.read_csv(file, sep=';')
                        elif df.shape[1] == 1: df = pd.read_csv(file, sep='\s+')
                    
                    df.index.name = filename
                    list_of_df.append(df)
                else:
                    logging.error(f"Only supported extensions: {','.join(['.parquet','.csv'])}")
            except Exception:
                logging.error(f"Cant find or convert data to format: {ext}")

        result = aj.join(*list_of_df, how=how, verbose=verbose)
        
        if isinstance(result, pd.DataFrame):
            if not output: output = '_'.join([os.path.splitext(os.path.basename(file))[0] for file in files]) + first_file_ext
            filename, ext = os.path.splitext(os.path.basename(output))

            print(result)

            if ext == '.parquet':
                result.to_parquet(output)
            elif ext == '.csv':
                result.to_csv(output, index_label='Index')
            else:
                raise Exception("No output file extension is given.")
    except Exception as e:
        logging.error(f"Some error occurred: {e}")

if __name__ == "__main__":
    print("""
 PANDAS
     _         _            _       _       
    / \  _   _| |_ ___     | | ___ (_)_ __  
   / _ \| | | | __/ _ \ _  | |/ _ \| | '_ \ 
  / ___ \ |_| | || (_) | |_| | (_) | | | | |
 /_/   \_\__,_|\__\___/ \___/ \___/|_|_| |_|
                                            
          """)
    main()