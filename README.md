# BNSW Network Scanner

A Python-based desktop network scanning application similar to Zenmap, providing a user-friendly GUI for Nmap scanning operations.

## Features

- **Multiple Scan Types**: Quick, Full, Ping, Service, OS Detection, and Comprehensive scans
- **Real-time Progress Monitoring**: Track scan progress with visual indicators
- **Network Visualization**: Interactive network map showing discovered hosts
- **Result Management**: Save, export, and review scan results
- **Dark/Light Theme**: Choose your preferred visual theme
- **Scan History**: Access previous scan results

## Requirements

- Python 3.10+
- Nmap (must be installed separately and available in PATH)
- Administrator/root privileges for certain scan types (OS Detection, Comprehensive)

## Installation

1. Ensure Nmap is installed on your system and available in your PATH
   - Windows: Download and install from [nmap.org](https://nmap.org/download.html)
   - Linux: `sudo apt install nmap` or equivalent for your distribution
   - macOS: `brew install nmap` (requires Homebrew)

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python -m BNSW
   ```

## Scan Types

| Profile | Description | Nmap Arguments | Admin Required |
|---------|-------------|----------------|---------------|
| Quick | Fast scan of common ports | `-T4 -F` | No |
| Full | Scan all 65535 ports | `-T4 -p-` | No |
| Ping | Only check if hosts are online | `-sn` | No |
| Service | Detect service versions | `-sV` | No |
| OS Detection | Identify operating systems | `-O` | Yes |
| Comprehensive | Full scan with service detection, OS detection, and traceroute | `-T4 -A -v` | Yes |

## Usage Guide

### Basic Scanning

1. Enter a target IP, hostname, or CIDR range (e.g., `192.168.1.1`, `example.com`, or `192.168.1.0/24`)
2. Select a scan profile from the dropdown
3. Click "Start Scan"
4. View results in the host and port tables

### Advanced Features

- **Network Map**: Switch to the Network Map tab to visualize discovered hosts
- **Save Results**: Use File > Save Results to export scan data as JSON
- **History**: Access previous scan results in the History tab
- **Theme**: Change appearance via View > Theme

## Troubleshooting

### Common Issues

- **"Nmap Not Found" Error**: Ensure Nmap is installed and in your system PATH
- **Permission Denied for OS Scans**: Run the application with administrator/root privileges
- **No Hosts Found**: Check your network connection and firewall settings

### Running with Admin Privileges

- **Windows**: Right-click the application shortcut and select "Run as administrator"
- **Linux/macOS**: Use `sudo` when starting the application

## Development

BNSW is built with:
- PyQt5 for the GUI
- SQLite with peewee ORM for data storage
- python-nmap for Nmap integration

The application follows a modular architecture:
- `core/`: Core scanning functionality
- `data/`: Database models and repositories
- `ui/`: User interface components
- `utils/`: Utility functions
- `plugins/`: Plugin system (extensible)

## License

This software is provided for educational and ethical use only.
