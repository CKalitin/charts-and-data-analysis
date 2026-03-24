# Electrolyzer cost and efficiency data
# (Efficiency kWh/kgH2, Capex $/kW, Company, Technology, Year, estimated-efficiency flag)

handmer_x = [48.362195, 48.609146, 49.053659, 49.564024, 50.304878,
             51.753659, 53.597561, 54.354878, 55.968293, 61.220122, 64.2, 72.810366]
handmer_y = [1882.917466, 1641.074856, 1389.635317, 1207.293666, 1086.372361,
             923.224568, 796.545106, 767.754319, 621.880998, 414.587332, 355.086372, 230.326296]

stack_points = [
    (50, 1050, 'EH2', 'PEM', 2022, 1),                     # EH2, Stack?, no prediction
]

plant_points = [
    (53,   1500, 'Hyto-Life / DOE',  'AEM',      2023, 1),       # Hyto-Life / DOE, Plant?, no prediction
    (50,   2147, 'Hyto-Life / DOE',  'PEM',      2023, 1),       # Hyto-Life / DOE, Plant?, no prediction
    #(40,   3000, 'Hyto-Life / DOE', 'SOEC',     2023, 1),       # Hyto-Life / DOE, Plant?, no prediction - makes graph too big
    (53,   1000, 'pMR',        'AEM',      2026, 1),       # pmarketresearch, Plant, no prediction
    (50,   1700, 'pMR',        'PEM',      2026, 1),       # pmarketresearch, Plant, no prediction
    (55,    800, 'pMR',        'Alkaline', 2026, 1),       # pmarketresearch, Plant, no prediction
    (56,   1700, 'IEA',        'PEM',      2022, 0),       # IEA, Plant?, no prediction
]

stack_estimate_points = [
    (55,   250, 'Versogen', 'Alkaline', 2030, 1),          # Versogen, Stack, prediction
    (48.9, 353, 'US DOE',  'Alkaline', 2025, 0),          # US DOE Est., Stack, prediction
    (53,   200, 'Verdagy', 'AEM',      2030, 1),          # Verdagy, Stack?, prediction
    (50,   300, 'EH2',     'PEM',      2026, 1),          # EH2, Stack?, prediction
    (78.89,    20, 'Terraform', 'Alkaline', 2030, 0),        # Long-term estimate
]

plant_estimate_points = [
    (54.4, 640, 'Enapter', 'AEM',      2025, 0),          # Enapter, Unclear/Plant?, prediction
    (54.3, 460, 'Ionomr',  'AEM',      2025, 0),          # Ionomr, Plant, prediction
    (54.3, 300, 'Ionomr',  'AEM',      2030, 0),          # Ionomr, Unclear/Plant?, prediction
    (53.7, 610, 'US DOE',  'Alkaline', 2025, 0),          # US DOE Est., Plant, prediction
    (55,   775, 'Verdagy', 'Alkaline', 2025, 1),          # Verdagy, Plant?, prediction
    (54.5, 850, 'EH2',     'PEM',      2030, 0),          # EH2, Plant?, prediction
]
