import pandas as pd
import json

def run_etl_pipeline():
    print("Starting ETL Pipeline: basic_patient_etl")
    

    # --- Node: source_1 (Type: data_source) ---


    print("Extracting from CSV: patients.csv")
    df_source_1 = pd.read_csv("patients.csv")




    # --- Node: transform_1 (Type: transform) ---

    print("Applying transformations...")
    # Pass data through transforms
    
    # Op: filter
    
    



    # --- Node: destination_1 (Type: destination) ---


    print("Loading to database table: patients_clean")
    # Add DB load logic here




    print("ETL Pipeline completed.")

if __name__ == "__main__":
    run_etl_pipeline()