# installResources.ps1
# Skrypt instalacji zależności projektu
# Szymon Wypler | 60822

Write-Host "Instalacja zależności projektu..."

pip install PyQt6
pip install pyyaml
pip install pyinstaller

Write-Host "Instalacja zakończona."
