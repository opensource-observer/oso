"""
Run this script on an excel file to generate a json with all grant data
"""

import openpyxl
import pandas as pd

# download from the source Google Sheet
inputExcelFile = "data/govgrants/Optimism GovFund Grants_ Public Distribution Tracking.xlsx"
outputJsonFile = "data/govgrants/Optimism_GovFund_PublicTracker.json"

# assignments for normalizing the data
mappings = [
    {
        "sheet": "Status Key",
        "ignore": True
    },
    {
        "sheet": "Grants Season 1",
        "mapping": {
            "Project Name": "Project Name",
            "Status": "Status",
            "Distribution Date": "Date",
            "Amount (OP)": "Amount",
            "L2 Address": "Address",
            "Proposal Link": "Link"
        },
        "fills": ["Cycle #"],
        "tags": {
            "Cycle #": {
                "Cycle 1 (Phase 0)": "Cycle 1 (Phase 0)",
                "Cycle 2 (Phase 1)": "Cycle 2 (Phase 1)",               
                "Cycle 3 (Phase 1)": "Cycle 3 (Phase 1)",
                "Cycle 4 (Phase 1)": "Cycle 4 (Phase 1)"
            },
            "Incentive Program Launched?": {"Yes": "Incentive Program Launched"}                    
        }
    },
    {
        "sheet": "Grants Season 2",
        "mapping": {
            "Project Name": "Project Name",
            "Status": "Status",
            "Distribution Date": "Date",
            "Amount (OP)": "Amount",
            "L2 Address": "Address",
            "Proposal Link": "Link"
        },
        "fills": ["Cycle #"],
        "tags": {
            "Cycle #": {
                "Cycle 6 (Phase 1)": "Cycle 6 (Phase 1)",
                "Cycle 7 (Phase 1)": "Cycle 7 (Phase 1)",
                "Cycle 8 (Phase 1)": "Cycle 8 (Phase 1)",                
            },
            "Incentive Program Launched?": {"Yes": "Incentive Program Launched"}                    
        }
    },
    {
        "sheet": "Grants Season 3",
        "skipRows": 1,
        "mapping": {
            "Project Name": "Project Name",
            "Status": "Status",
            "Initial Distribution Date": "Date",
            "Total Amount (OP)": "Amount",
            "L2 Address": "Address",
            "Proposal Link": "Link"
        },
        "fills": ["Cycle #"],
        "tags": {
            "Cycle #": {
                "Cycle 10": "Cycle 10",
                "Cycle 11": "Cycle 11"
            },
            "Incentive Program Launched?": {"Builders": "Builders Grant"}                    
        }
    },
     {
        "sheet": "Grants Season 4",
        "skipRows": 1,
        "mapping": {
            "Project Name": "Project Name",
            "Status": "Status",
            "Initial Distribution Date": "Date",
            "Total Amount (OP)": "Amount",
            "L2 Address": "Address",
            "Proposal Link": "Link"
        },
        "fills": ["Cycle #"],
        "tags": {
            "Cycle #": {
                "Cycle 13": "Cycle 13",
                "Cycle 14": "Cycle 14",
                "Cycle 15": "Cycle 15"
            },
            "Incentive Program Launched?": {
                "Builders": "Builders Grant",
                "Growth": "Growth Grant",
                "RFG1": "RFG1",
                "RFG2": "RFG2",
                "RFG3": "RFG3",
                "RFG4": "RFG4",
                "RFG5": "RFG5",
                "RFG6": "RFG6",
                "RFG7": "RFG7",
                "RFG8": "RFG8"
            }                    
        }
    },
    {
        "sheet": "Missions Season 4",
        "mapping": {
            "Project Name": "Project Name",
            "Status": "Status",
            "Distribution Date": "Date",
            "Amount (OP)": "Amount",
            "L2 Address": "Address",
            "Proposal Link": "Link"
        },
        "fills": ["Cycle #"],
        "tags": {
            "Cycle #": {
                "Cycle 13": "Cycle 13"
            },
            "Intent": {
                "Intent 1": "Intent 1",
                "Intent 2": "Intent 2",
                "Intent 3": "Intent 3",
                "Intent 4": "Intent 4"
            },
            "Trust Tier": {
                "Fledgling": "Fledgling",
                "Phoenix": "Phoenix",
                "Ember": "Ember"  
            },
            "Incentive Program Launched?": {
                "Builders": "Builders Grant"
            }                    
        }
    }
]

# load the excel file
newWorkbook = openpyxl.load_workbook(inputExcelFile)
sheetNames = newWorkbook.sheetnames

# processing script for reading each sheet
def process(sheet_num):
    
    sheetData = mappings[sheet_num]
    sheetName = sheetData.get('sheet')    
    skipRows = sheetData.get('skipRows', 0)
    mapping = sheetData.get('mapping', {})
    fills = sheetData.get('fills', [])
    tags = sheetData.get('tags', {})
    
    df = pd.read_excel(inputExcelFile, sheet_name=sheetName, skiprows=skipRows)
    df.columns = [c.strip() for c in df.columns]

    for fillCol in fills:
        df[fillCol].fillna(method='ffill', inplace=True)

    tagValues = []    
    for _, row in df.iterrows():
        thisRowTags = [sheetName]
        for tagCol, tapMapping in tags.items():
            for key, val in tapMapping.items():
                if row[tagCol] == key:
                    thisRowTags.append(val)
        #tagValues.append(",".join(thisRowTags))
        tagValues.append(thisRowTags)

    df = df[mapping.keys()].rename(columns=mapping)
    df['Tags'] = tagValues

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').fillna(0)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df['Status'].fillna("Unknown", inplace=True)
    
    df = df[(~df['Amount'].isna()) & (~df['Address'].isna())]
    
    return df

# process each sheet
dfs = []
for i in range(len(sheetNames)):
    if mappings[i].get('ignore'):
        continue        
    print(mappings[i]['sheet'])
    dfs.append(process(i))

# concat and dump to json
df = pd.concat(dfs, ignore_index=True, axis=0)
df.to_json(outputJsonFile, indent=4, orient='records')    