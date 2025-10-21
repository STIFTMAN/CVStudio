Remove-Item -Recurse -Force .\.venv -ErrorAction SilentlyContinue
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
if (Test-Path requirements.txt) {
  python -m pip install -r requirements.txt
}
echo "Setup Done"
exit
