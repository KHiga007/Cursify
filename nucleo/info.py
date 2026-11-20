"""Cursify: crea y aplica temas de cursores al estilo Windows en Linux Mint."""

__version__ = "1.0.1"
APP_NAME = "Cursify"


def migrate_old_config():
    """La app antes se llamaba PunteroFácil: copia sus presets y ajustes a ~/.config/cursify
    la primera vez (la carpeta vieja no se toca)."""
    import os
    import shutil
    new = os.path.expanduser("~/.config/cursify")
    old = os.path.expanduser("~/.config/punterofacil")
    if os.path.isdir(old) and not os.path.exists(new):
        try:
            shutil.copytree(old, new, symlinks=True)
        except OSError:
            pass


