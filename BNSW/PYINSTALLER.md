# BNSW Network Scanner - PyInstaller Instructions

## Building the Executable

The BNSW Network Scanner can be packaged as a standalone executable using PyInstaller. This allows users to run the application without needing to install Python or any dependencies.

### Prerequisites

Before building the executable, ensure you have the following installed:
- Python 3.10+
- PyInstaller (`pip install pyinstaller`)
- All dependencies listed in requirements.txt

### Building Steps

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. Run the build script:
   ```
   python build.py
   ```

3. The executable will be created in the `dist` directory.

### Platform-Specific Notes

#### Windows
- The executable will be named `BNSW.exe`
- For OS Detection and Comprehensive scans, right-click the executable and select "Run as administrator"

#### Linux
- The executable will be named `BNSW`
- For OS Detection and Comprehensive scans, run with sudo: `sudo ./BNSW`

#### macOS
- The executable will be named `BNSW`
- For OS Detection and Comprehensive scans, run with sudo: `sudo ./BNSW`

## Manual PyInstaller Command

If the build script doesn't work for your environment, you can manually run PyInstaller with the following command:

### Windows
```
pyinstaller --name=BNSW --onefile --windowed --icon=BNSW/resources/icon.ico --add-data=BNSW/resources;BNSW/resources --hidden-import=peewee --hidden-import=PyQt5.sip BNSW/__main__.py
```

### Linux/macOS
```
pyinstaller --name=BNSW --onefile --windowed --icon=BNSW/resources/icon.png --add-data=BNSW/resources:BNSW/resources --hidden-import=peewee --hidden-import=PyQt5.sip BNSW/__main__.py
```

## Troubleshooting

If you encounter issues with the executable:

1. **Missing Dependencies**: Ensure all required packages are installed before building
2. **Permission Issues**: Make sure to run with administrator/root privileges for certain scan types
3. **Antivirus Blocking**: Some antivirus software may flag the executable; add an exception if needed
4. **Nmap Not Found**: Ensure Nmap is installed and in the system PATH
