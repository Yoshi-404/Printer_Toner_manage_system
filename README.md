# Printer Toner Management System

A web-based system designed to automatically monitor network printers, extract supply levels via SNMP, and manage inventory of toner cartridges. Built with Django, this application provides IT departments with a centralized dashboard to track critical supplies and prevent printing downtime.

## Key Features

- **Automated SNMP Monitoring:** Connects to network printers (HP, Brother, Samsung, etc.) using standard and proprietary Printer MIB OIDs to fetch exact toner percentages and page counts.
- **Dynamic Dashboard:** Real-time visibility into the status of all registered printers, highlighting devices with critically low toner or offline status.
- **Inventory Control:** Built-in module to manage physical toner stock. Automatically warns when a specific toner model is running low.
- **Replacement Tracking:** Records all manual and automatic toner replacements, generating a history log to analyze consumption patterns over time.
- **Background Processing:** Collects data asynchronously to prevent UI blocking and can be integrated with system schedulers (Cron/Systemd) for continuous 24/7 monitoring.

## Technical Stack

- **Backend:** Python 3.10+, Django 4+
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **Protocol:** SNMP (via `snmpwalk`)
- **Database:** SQLite (Default, configurable to PostgreSQL/MySQL)

## Prerequisites

- Python 3.10 or higher
- The `snmpwalk` utility installed on the host operating system:
  - Linux/Ubuntu: `sudo apt install snmp`
  - macOS: `brew install net-snmp`
  - Windows: Requires Net-SNMP binaries installed and added to the system PATH.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Yoshi-404/Printer_Toner_manage_system.git
   cd Printer_Toner_manage_system
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Apply database migrations:
   ```bash
   python manage.py migrate
   ```

5. Create an administrative user:
   ```bash
   python manage.py createsuperuser
   ```

6. Start the development server:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

## Configuration and Usage

1. Access the Django Admin panel at `http://localhost:8000/admin/` and log in with your superuser credentials.
2. Navigate to the **Toner** section to register your network printers (IP, Sector, SNMP Community). The system will automatically detect the Printer Brand and Model on the first successful scan.
3. Register your physical Toner Models and set their current stock levels.
4. Access the main dashboard at `http://localhost:8000/` to monitor the real-time status of your printing infrastructure.

## Automated Monitoring (Cron)

To ensure the system continuously updates toner levels without manual intervention, configure a cron job on your server to execute the collection script every 3 hours:

```bash
0 */3 * * * cd /path/to/Printer_Toner_manage_system && venv/bin/python manage.py coletar_toner
```

## Demo Mode

If you wish to test the interface without configuring physical network printers, you can launch the application in Demo Mode. This mode generates simulated devices and randomizes toner consumption over time.

```bash
# Populate the database with simulated printers
python manage.py popular_demo

# Run the server in Demo Mode
TONER_DEMO=1 python manage.py runserver
```
*(On Windows CMD use: `set TONER_DEMO=1 && python manage.py runserver`)*

## License

This project is open-source and available under the MIT License.
