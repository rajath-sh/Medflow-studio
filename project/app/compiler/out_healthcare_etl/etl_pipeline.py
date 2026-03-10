import pandas as pd
import json

def run_etl_pipeline():
    print("Starting ETL Pipeline: Healthcare ETL Pipeline")
    

    # --- Node: trigger_node (Type: trigger) ---



    # --- Node: source_csv (Type: data_source) ---


    print("Extracting from CSV: data/incoming/patients_daily.csv")
    df_source_csv = pd.read_csv("data/incoming/patients_daily.csv")




    # --- Node: transform_patient (Type: transform) ---

    print("Applying transformations...")
    # Pass data through transforms
    
    # Op: convert_unit
    
    
    # Op: rename
    
    df_transform_patient = df_transform_patient.rename(columns={"height": "height_cm"})
    
    
    # Op: dedup
    
    



    # --- Node: dest_db (Type: destination) ---


    print("Loading to database table: patient_records")
    # Add DB load logic here




    print("ETL Pipeline completed.")

if __name__ == "__main__":
    run_etl_pipeline()