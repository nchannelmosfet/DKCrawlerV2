#py -3-64 -m pip install virtualenv
#py -3-64 -m virtualenv venv
#.\venv\Scripts\activate
#pip install -r requirements.txt
#playwright install

$items_to_hide = ".gitignore", ".git", "requirements.txt", "venv", ".idea", "dkcrawlerv2", 'test', 'setup.py'
foreach ($path in $items_to_hide) {
	if (Test-Path -path $path){
		$item = Get-Item $path -Force
		$item.attributes="Hidden"
	}
}
