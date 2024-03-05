import pandas as pd
import pandas_auto_join as aj

# Read dataframes
df1 = pd.read_csv('./data/flights.csv', sep=';')
df2 = pd.read_csv('./data/bag.csv', sep=';')
df3 = pd.read_csv('./data/airports.csv', sep=';')

# Join dataframes
df_final = aj.join(df1, df2, df3, how='left')

# Print final result
print(df_final)