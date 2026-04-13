# Crop Data Preprocessing Report

## Dataset Scope
- Raw dataset shape: `(35000, 39)`
- Proposal-scoped dataset shape: `(17715, 11)`
- Target column: `recommended_crop`
- Environmental features used: `soil_ph, nitrogen, phosphorus, potassium, annual_rainfall_mm, avg_temperature_C, avg_humidity_pct, altitude_m`
- Crop classes kept to match the proposal scope: `maize, beans, cassava, rice, irish_potato`

## Step-by-Step Preprocessing
1. Loaded `ahs_dataset_nisr.csv`.
2. Filtered the dataset to the five crops named in the proposal.
3. Selected the eight environmental features described in Chapter Three.
4. Checked missing values in the modeling features.
5. Applied district-level mean imputation with median fallback where needed.
6. Encoded the crop target using label encoding.
7. Standardized the eight numeric features using `StandardScaler`.
8. Saved the processed dataset and graphs to the `outputs` folder.

## Missing-Value Check Before Imputation
```text
                    missing_count
soil_ph                         0
nitrogen                        0
phosphorus                      0
potassium                       0
annual_rainfall_mm              0
avg_temperature_C               0
avg_humidity_pct                0
altitude_m                      0
```

## Missing-Value Check After Imputation
```text
                    missing_count
soil_ph                         0
nitrogen                        0
phosphorus                      0
potassium                       0
annual_rainfall_mm              0
avg_temperature_C               0
avg_humidity_pct                0
altitude_m                      0
```

## Class Distribution
```text
                  count
recommended_crop       
irish_potato       5390
cassava            4687
rice               3030
maize              2577
beans              2031
```

## Label Encoding Map
- `beans` -> `0`
- `cassava` -> `1`
- `irish_potato` -> `2`
- `maize` -> `3`
- `rice` -> `4`

## Raw Feature Summary
```text
         soil_ph   nitrogen  phosphorus  potassium  annual_rainfall_mm  avg_temperature_C  avg_humidity_pct  altitude_m
count  17715.000  17715.000   17715.000  17715.000           17715.000          17715.000         17715.000   17715.000
mean       6.004      0.354       0.121      0.358             901.441             21.989            74.946    1500.841
std        0.599      0.174       0.067      0.208             177.690              2.772             8.954     200.421
min        4.000      0.020       0.005      0.020             300.000             11.040            40.500    1035.000
25%        5.600      0.231       0.073      0.204             780.650             20.120            68.900    1363.000
50%        6.000      0.352       0.120      0.350             902.700             21.980            74.900    1509.000
75%        6.410      0.471       0.166      0.502            1020.500             23.880            81.000    1649.000
max        8.370      1.014       0.419      1.260            1556.700             30.000            98.000    1976.000
```

## Scaled Feature Summary
```text
         soil_ph   nitrogen  phosphorus  potassium  annual_rainfall_mm  avg_temperature_C  avg_humidity_pct  altitude_m
count  17715.000  17715.000   17715.000  17715.000           17715.000          17715.000         17715.000   17715.000
mean       0.000     -0.000      -0.000     -0.000              -0.000              0.000             0.000      -0.000
std        1.000      1.000       1.000      1.000               1.000              1.000             1.000       1.000
min       -3.343     -1.917      -1.741     -1.624              -3.385             -3.949            -3.847      -2.324
25%       -0.674     -0.704      -0.721     -0.740              -0.680             -0.674            -0.675      -0.688
50%       -0.007     -0.009      -0.017     -0.040               0.007             -0.003            -0.005       0.041
75%        0.677      0.675       0.673      0.690               0.670              0.682             0.676       0.739
max        3.947      3.797       4.465      4.328               3.688              2.890             2.575       2.371
```

## Graphs Generated
- `outputs/graphs/crop_distribution.png`
- `outputs/graphs/feature_correlation_heatmap.png`
- `outputs/graphs/raw_feature_boxplots.png`
- `outputs/graphs/scaled_feature_boxplots.png`
