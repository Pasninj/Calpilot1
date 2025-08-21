#!/usr/bin/env bash
# 🚀 Script de build pour Render

pip install -r requirements.txt
playwright install --with-deps
