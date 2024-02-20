import pandas as pd
import pandas_auto_join as aj

# Read dataframes
df1 = pd.read_csv('./data/flight.csv')
df2 = pd.read_csv('./data/bag.csv')

# Join dataframes
df_final = aj.join(df1, df2)

# Print final result
print(df_final)