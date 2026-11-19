#!/usr/bin/env python3
"""Punto de entrada de Cursify: python3 cursify.py [carpeta]"""
import sys

from nucleo.info import migrate_old_config
from interfaz.app import main

migrate_old_config()
sys.exit(main())
