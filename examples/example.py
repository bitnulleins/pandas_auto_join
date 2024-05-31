import pandas_auto_join as aj
import pandas as pd

print(f"Version: {aj.__version__}")

# Read dataframes
df1 = pd.read_csv('./datasets/flights/flights.csv', sep=',')
# Worked well
df2 = pd.read_csv('./datasets/flights/flight_times.csv', sep=',')
# Worked well
df3 = pd.read_csv('./datasets/flights/baggage.csv', sep=',')
# Worked well
df4 = pd.read_csv('./datasets/flights/airlines_duplicates.csv', sep=',')
# Data Conflict!
df5 = pd.read_csv('./datasets/flights/aircrafts.csv', sep=',')

# Join dataframes
df = aj.join(
    df1, df2, df3, df4, df5,
    how='inner',
    similarity_strategy='ratio',
    similarity_threshold=0.5,
    verbose=1
)

# Print final result
print(df)