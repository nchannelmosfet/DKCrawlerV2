# Digikey Crawler v2

## Install Tools

### Download and install [Python 3](https://www.python.org/):
- Check "Install launcher for all users (recommended)" box
- Check "Add Python 3.10 to PATH"
- Click Customize installation
    - Check all "Optional Features"
    - Check all "Advanced Options"
    - Customize install location: set to "C:\Python310_64"
- Next
- Finish

### Download and install [Git](https://git-scm.com/downloads).
Just keep click "Next" and install with all default options. 

### Download and install [PowerShell 7](https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-windows?view=powershell-7.2)
- Next
- Next
- Check these two additional boxes:
    - Add 'Open here' context menus to Explorer
    - Add "Run with PowerShell 7" context menu for PowerShell files
- Use default options for the remainder of the installation

### Download and install [PyCharm Community Edition](https://www.jetbrains.com/pycharm/)
- Next
- Next
- Check these two additional boxes:
	- Check "Update Context Menu" -> `Add "Open Folder as Project"`
	- Check "Create Associations" -> ".py"
- Next
- Install

### PyCharm Configuration
- File -> Settings -> Tools -> Terminal 
- Set Shell path to: "C:\Program Files\PowerShell\7\pwsh.exe"
- Ok or Apply

## Install Digikey Crawler v2
- Run PowerShell 7 as Administrator 
  - Click Windows Search icon, type "PowerShell 7"
  - Run "PowerShell 7 (x64)" as Administrator
- Run the following commands on PowerShell 7
  ```PowerShell
  # change directory (aka folder) to C:/
  # use your desire directory to store the project
  cd /
  
  # create the python-projects directory 
  mkdir python-projects
  
  # change directory to C:/python-projects/
  cd python-projects
  
  # clone the repo
  git clone https://github.com/nchannelmosfet/DKCrawlerV2.git
  
  # change directory to C:/python-projects/DKCrawlerV2
  cd DKCrawlerV2
  
  # Run install.ps1 script to install the dependencies
  .\install.ps1
  
  # open folder in File Explorer
  explorer.exe .
  ```
  
- In the newly opened File Explorer windows
  - Right click 
  - Click "Open Folder as PyCharm Community Edition Project"

- Configure Virtual Environment in PyCharm
  - Files -> Settings -> Project: DKCrawlerV2 -> Python Interpreter -> "Gear Icon" -> Add -> "Existing Environment" -> Apply and Ok
  - Wait for indexing to complete
  
- Finally, you can run scripts in AppSubcat or AppVendor
