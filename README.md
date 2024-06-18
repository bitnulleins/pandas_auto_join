<p align="center">
<img src="./assets/logo.svg" width="300" />
</p>

<p align="center">
<img src="https://img.shields.io/badge/version-1.0.0-blue" /> <img src="https://img.shields.io/github/license/bitnulleins/pandas_auto_join" />  <img src="https://img.shields.io/github/size/bitnulleins/pandas_auto_join/src%2Fpandas_auto_join%2F__init__.py">
</p>

# Pandas AutoJoin

With the help of this lightweight framework it is possible to **automatically join two or more large dataframes** together. _Pandas AutoJoin_ offers the following features:

-   Simple usage
-   Automatic primary and foreign key detection<br />(technical and composite keys)
-   Detect and solve some data conflicts<br />(Misspellings, Homonyms, Synonyms, Datatypes...)
-   Command Line Interface ([CLI](#command-line-interface-cli))

The framework simplifies the automation of data acquisition a part of Data Science Life Cycle. It extends the benefits of AutoML and makes it more accessible to machine learning beginners.

# Content

- [Requirements](#requirements)
- [Usage](#usage)
- [Documentation](#documentation)
- [Command Line Interface (CLI)](#command-line-interface-cli)
- [Example](#example)
- [Paper (Citation)](#paper-citation)

## Requirements

- [x] Python >= 3.8
- [x] pandas
- [x] click
- [x] tqdm
- [x] Levenshtein

## Usage

Let `df1` be the reference `Pandas` dataframe table and `df2` other input tables for join. Then the automatic join can perform easliy by:

```python
import pandas as pd
import pandas_auto_join as aj
df1 = pd.read_csv('./example/datasets/flights/flights.csv')
df2 = pd.read_csv('./example/datasets/flights/airlines.csv')
df = aj.join(df1, df2)
print(df)
```

or as CLI:

```shell
python -m pandas_auto_join './example/datasets/flights/flights.csv' './example/datasets/flights/airlines.csv'
```

_Debug Mode:_ You can change the `DEBUG` stage in [config.py](./src/pandas_auto_join/config.py) file.

## Documentation

```python
def join(
    *args: Tuple[pd.DataFrame], 
    how: str = 'inner',
    strategy: str = 'levenshtein',
    threshold: float = 0.5,
    verbose: int = 0
)
```

Parameters

* ***args : *Tuple[pd.DataFrame]***<br />Dataframes, at least two for join.
* **how : *str*, default = 'inner'**<br />How join should perform *inner*, *left* or *outer*.
* **strategy : *str*, default = 'levenshtein'**<br />Similarity strategy for detect string similarity.
  1. *levenshtein*: [Levenshtein](https://en.wikipedia.org/wiki/Levenshtein_distance) edit based distance
  2. *jaro*: [Jaro](https://en.wikipedia.org/wiki/Jaro–Winkler_distance) distance
* **threshold : *float*, default = 0.5**:<br />How similar should strings be? Value between 0.0 and 1.0.
  1. 0.0 = No similarity check
  2. 1.0 = Equi-join, strings has to be equal
* **verbose : *int*, default = 0**:<br />Print informative messages while run (1=yes, 0=no)

## Command Line Interface (CLI) 

```shell
 PANDAS
     _         _            _       _       
    / \  _   _| |_ ___     | | ___ (_)_ __  
   / _ \| | | | __/ _ \ _  | |/ _ \| | '_ \ 
  / ___ \ |_| | || (_) | |_| | (_) | | | | |
 /_/   \_\__,_|\__\___/ \___/ \___/|_|_| |_|
                                            
          
Usage: python -m pandas_auto_join [OPTIONS] FILES...

  Command to load and auto join two or more dataframes. Actually support
  PARQUET and CSV files.

Options:
  -h, --how [left|inner|outer]    Pandas merge type.  [default: inner]
  -ss, --strategy [levenshtein|jaro]
                                  Algorithm for calculating similarity score.
                                  [default: levenshtein]
  -st, --threshold FLOAT RANGE    Threshold for similiarity of strings. 1 =
                                  Equi-join. 0 = Accept all.  [default: 0.5;
                                  0<=x<=1]
  -o, --output TEXT               Name of output file with file extension.
  -v, --verbose INTEGER RANGE     Print feedback while running.  [default: 0;
                                  0<=x<=1]
  --help                          Show this message and exit.
```


## Example

An example with five datasets and different data conflicts:

- Different column names for each table
- Detect `Flight` and `Date` are composite keys for `FLNo`and `FLDate`
- `FLNo` has white spaces and `Flight` not
- `FLDate` different format than `Date`
- `Bag` is foreign key (number) for `bagid`
- `Airline` has misspellings in names `Airline`

**[Flights](./example/datasets/flights/flights.csv) (Reference table)**

| Flight  | Date       | Bag   | Airline   |
| ------- | ---------- | ----- | --------- |
| ABC1234 | 2024-02-01 | 43242 | Luthansa  |
| ABC1234 | 2024-02-02 | 34234 | Eurowoing |
| ...     | ...        | ...   | ...       |

**[Transcation Data: Flight times](./example/datasets/flights/flight_times.csv)**

| FLNo     | FLDate     | Time  |
| -------- | ---------- | ----- |
| ABC 1234 | 02/01/2024 | 08:00 |
| ABC 1234 | 02/02/2024 | 13:00 |
| ...      | ...        | ...   |

**[Transcation Data: Baggage](./example/datasets/flights/baggage.csv)**

| bagid    | bagcount |
| -------- | -------- |
| 43242    | 143      |
| 34234    | 89       |
| ...      | ...      |

**[Master data: Airline](./example/datasets/flights/airlines.csv)**

| Airline   | Code |
| --------- | ---- |
| Lufthansa | LH   |
| Eurowings | EW   |
| ...       | ...  |

**✅ Result table**

```python
import pandas_auto_join as aj
df = aj.join(flights, flight_times, baggage, airlines)
```

| Flight  | Date       | Bag   | Airline   | _Time_ | _bagcount_ | _Code_ |
| ------- | ---------- | ----- | --------- | ------ | ---------- | ------ |
| ABC1234 | 2024-02-01 | 43242 | Luthansa  | 08:00  | 143        | LH     |
| ABC1234 | 2024-02-02 | 34234 | Eurowoing | 13:00  | 89         | EW     |
| ...     | ...        | ...   | ...       | ...    | ...        | ...    |


## Paper (Citation)

> [!NOTE]  
> Paper on the framework with benchmarks has not yet been published, but will be submitted later.