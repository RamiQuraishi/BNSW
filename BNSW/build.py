#!/usr/bin/env python3
"""
BNSW Build Script
----------------
This script builds the BNSW application using PyInstaller.
"""

import os
import sys
import shutil
import subprocess
import platform

def main():
    """Main function."""
    print("Building BNSW Network Scanner...")
    
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create build directory
    build_dir = os.path.join(current_dir, 'build')
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
    
    # Create dist directory
    dist_dir = os.path.join(current_dir, 'dist')
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    
    # Determine platform-specific settings
    if platform.system() == 'Windows':
        icon_path = os.path.join(current_dir, 'BNSW', 'resources', 'icon.ico')
        exe_name = 'BNSW.exe'
        hidden_imports = ['peewee', 'PyQt5.sip']
    else:
        icon_path = os.path.join(current_dir, 'BNSW', 'resources', 'icon.png')
        exe_name = 'BNSW'
        hidden_imports = ['peewee', 'PyQt5.sip']
    
    # Create PyInstaller command
    cmd = [
        'pyinstaller',
        '--name=BNSW',
        '--onefile',
        '--windowed',
        f'--icon={icon_path}',
        '--add-data=BNSW/resources:BNSW/resources',
        '--clean',
        '--noconfirm'
    ]
    
    # Add hidden imports
    for imp in hidden_imports:
        cmd.append(f'--hidden-import={imp}')
    
    # Add main script
    cmd.append(os.path.join(current_dir, 'BNSW', '__main__.py'))
    
    # Run PyInstaller
    print("Running PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Build completed successfully. Executable is at: {os.path.join(dist_dir, exe_name)}")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {str(e)}")
        return 1
    except Exception as e:
        print(f"Unexpected error during build: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
