from pathlib import Path
import subprocess

from molint import molint

def compile_mo(path, domain):
    lang = path.stem
    lang_dir = Path(f"frescobaldi/i18n/{lang}/LC_MESSAGES")
    lang_dir.mkdir(parents=True, exist_ok=True)
    out_file = lang_dir / f"{domain}.mo"
    subprocess.run(["msgfmt", "-o", out_file, path])
    molint(out_file)


for po in Path("i18n/frescobaldi").glob("*.po"):
    compile_mo(po, "frescobaldi")
for po in Path("i18n/userguide").glob("*.po"):
    compile_mo(po, "userguide")
