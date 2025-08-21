#!/bin/bash
# Installer les dépendances Python
pip install -r requirements.txt

# Installer Chromium localement pour l'utilisateur
PLAYWRIGHT_BROWSERS_PATH=~/.cache/ms-playwright playwright install chromium
