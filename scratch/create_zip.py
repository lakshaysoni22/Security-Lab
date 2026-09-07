import os
import zipfile

project_dir = "C:/Users/Acer/.gemini/antigravity-ide/scratch/LEAtTrace"
zip_path = "C:/Users/Acer/.gemini/antigravity-ide/scratch/LEAtTrace.zip"

print(f"Creating clean zip archive at {zip_path}...")

exclude_dirs = {"node_modules", "dist", ".git", "__pycache__", ".pytest_cache", ".venv", "venv"}
exclude_files = {".DS_Store", "LEAtTrace.db"}

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(project_dir):
        # Modify dirs in-place to exclude directories from walk
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file in exclude_files:
                continue
                
            file_path = os.path.join(root, file)
            # Calculate archive path relative to scratch directory to maintain parent directory structure
            arcname = os.path.relpath(file_path, os.path.dirname(project_dir))
            zipf.write(file_path, arcname)

print("Zip archive created successfully!")
