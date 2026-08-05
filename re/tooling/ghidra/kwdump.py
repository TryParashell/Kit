import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.container import SldprtArchive


def main():
    for name in sys.argv[1:]:
        hits = list((ROOT / ".rescratch").rglob(name + ".SLDPRT"))
        if not hits:
            hits = list((ROOT / "examples").rglob(name + ".SLDPRT"))
        if not hits:
            print(name, "missing")
            continue
        archive = SldprtArchive.open(hits[0])
        blob = archive.get("swXmlContents/KeyWords") or b""
        text = blob.decode("utf-8", "replace")
        print("===", name, hits[0].parent.name)
        for match in re.finditer(r"<([A-Za-z]+)([^>]*)/?>", text):
            tag, attrs = match.group(1), match.group(2)
            if tag in ("Keywords", "Configuration"):
                continue
            print(f"   {tag:16s} {attrs.strip()[:160]}")


if __name__ == "__main__":
    main()
