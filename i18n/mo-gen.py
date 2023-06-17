from pathlib import Path
import subprocess

for po in Path("i18n/frescobaldi").glob("*.po"):
    lang = po.stem
    combined = subprocess.run([
        "msgcat", "-o", "-", po, (Path("i18n/userguide") / lang).with_suffix(".po")
    ], capture_output=True, encoding="utf-8").stdout
    lang_dir = Path(f"frescobaldi_app/i18n/{lang}/LC_MESSAGES")
    lang_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["msgfmt", "-o", lang_dir / "frescobaldi.mo", "-"],
                   input=combined, encoding="utf-8")
