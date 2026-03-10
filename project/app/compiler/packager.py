import os
import shutil

def package_project(source_dir: str, output_zip_path: str):
    """
    Packages the generated project directory into a ZIP file.
    """
    if not os.path.exists(source_dir):
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    # shutil.make_archive adds the .zip extension itself, so we strip it if present
    base_name = output_zip_path
    if base_name.endswith('.zip'):
        base_name = base_name[:-4]
        
    archive_path = shutil.make_archive(base_name, 'zip', source_dir)
    print(f"[SUCCESS] Project packaged successfully: {archive_path}")
    return archive_path
