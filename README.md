<p align="center">
<img src="./assets/logo.svg" width="300" />
</p>

<p align="center">
<img src="https://img.shields.io/badge/version-0.1.3-blue" /> <img src="https://img.shields.io/github/license/bitnulleins/pandas_auto_join" /> 
</p>

# 🔄 Pandas AutoJoin

With the help of this lightweight framework it is possible to **automatically join two or more large dataframes** together. *Pandas AutoJoin* offers the following features:

* Simple usage
* Automatic primary and foreign key detection<br />(technical and combound keys)
* Automatic datatype detection
* Step-by-step description
* Command Line Interface ([CLI](#command-line-interface-cli))

The framework simplifies the automation of data acquisition a part of Data Science Life Cycle. It extends the benefits of AutoML and makes it more accessible to machine learning beginners.

## Installation

> [!NOTE]  
> Actually the framework **isn't** add to Python Package Index (pypi) yet.

```shell
pip install pandas-auto-join
```

Requirements:

* Python >= 3.8
* pandas
* click
* tqdm

### Usage

```python
import pandas_auto_join as aj
df = aj.join(df1, df2)
```

or as CLI:

```shell
python ./src/cli.py 'dataframe_path_1' 'dataframe_path_2'
```

*Debug Mode:* You can change the `DEBUG` stage in [config.py](./src/config.py) file.

### Example

**[Table 1](./example/data/flights.csv) (Left table)**

|FLIGHTNUMBER|DATE      |PASSENGER|
|------------|----------|---------|
|ABC 1234    |2024-02-01|232      |
|XYZ 1234    |2024-02-02|190      |
|DEF 343     |          |150      |

**[Table 2](./example/data/bag.csv) (Right table)**

Sucessfully joined `BAG.AMOUNT` column for exist value (`LEFTJOIN`)

|BAG.FLIGHT|BAG.FLIGHT_DATE|*BAG.AMOUNT*|
|---------|---------------|------------|
|ABC1234  |2024-02-01     |*120*       |
|XYZ1234  |2024-02-02     |*89*        |

It exist an non-technical combound key for `FLIGHTNUMBER`, `DATE` and `BAG.FLIGHT`, `BAG.FLIGHT_DATE`.

Execute AutoJoin by CLI:

```shell
python ./src/cli.py './example/data/flights.csv' './example/data/bag.csv' --output='./example/data/final.csv' --how='left'
```

**[Result tabel](./example/data/final.csv)**

|Index|FLUGNUMMER|ID   |PAX  |BAG.FLIGHT_DATE|*BAG.AMOUNT*|
|-----|----------|-----|-----|---------------|------------|
|0    |ABC 1234  |345.0|232.0|2024-02-01     |*120.0*     |
|1    |XYZ 1234  |23.0 |190.0|2024-02-02     |*89.0*      |
|2    |DEF 343   |1.0  |150.0|               |            |

### Command Line Interface (CLI)

```shell
 PANDAS
     _         _            _       _       
    / \  _   _| |_ ___     | | ___ (_)_ __  
   / _ \| | | | __/ _ \ _  | |/ _ \| | '_ \ 
  / ___ \ |_| | || (_) | |_| | (_) | | | | |
 /_/   \_\__,_|\__\___/ \___/ \___/|_|_| |_|
                                            
          
Usage: cli.py [OPTIONS] FILES...

  Command to load and auto join two or more dataframes. Actually support
  PARQUET and CSV files.

Options:
  -h, --how [left|inner|outer]  Pandas merge type.  [default: inner]
  -o, --output TEXT             Name of output file with file extension.
  -v, --verbose INTEGER         Print feedback while running.  [default: 0]
  --help                        Show this message and exit.                     Show this message and exit.
```
