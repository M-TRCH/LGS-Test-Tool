"""Verify every firmware image the exe will bundle. Exits non-zero on trouble.

    python tools/verify_blobs.py

`build_exe.ps1` runs this as its gate. The gate used to carry its OWN copy of
the expected hashes, beside the copy in `app/firmware_bundle.py`, and the two
drifted: the build script was never told about gateway v1.12.3, so a build
would pass while the newest bundled gateway image was still v1.12.2. Since the
UI offers the FIRST entry of a kind as its default, the tool would have
offered that older image as the obvious choice and quietly downgraded any
gateway running v1.12.3 -- removing the all_8 panel action the type-80
cabinet's front button is configured to use.

So there is one source of truth now, `firmware_bundle.IMAGES`, and this asks
it three questions:

  * does every image in the manifest load and match its recorded SHA-256,
  * is every .bin actually present in app/blobs accounted for by the manifest
    (an unlisted file is either a forgotten entry or a stray), and
  * is the default offered for each kind the NEWEST version in the manifest?

The last one is the check that would have caught this. A manifest is ordered
newest-first by convention, and a convention no one verifies is a comment.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import firmware_bundle as fb                             # noqa: E402

# Not a firmware image: Arduino's QSPI formatter, needed to prepare a
# factory-fresh Opta on site. It has no manifest entry by design.
NOT_FIRMWARE = {"qspiformat_opta.bin"}


def _ver(v: str):
    """(1, 12, 3) from 'v1.12.3', so 1.12.3 sorts above 1.9.0 -- a lexical
    compare once made v1.9.2 beat v1.10.0 in this project."""
    return tuple(int(n) for n in re.findall(r"\d+", v))


def main() -> int:
    problems: list = []

    listed = set()
    for im in fb.IMAGES:
        listed.add(im.blob)
        try:
            fb.load(im)
        except Exception as exc:                                  # noqa: BLE001
            problems.append(f"{im.blob}: {exc}")

    blobs_dir = Path(__file__).resolve().parent.parent / "app" / "blobs"
    for f in sorted(blobs_dir.glob("*.bin")):
        if f.name not in listed and f.name not in NOT_FIRMWARE:
            problems.append(f"{f.name}: in app/blobs but not in IMAGES")

    for missing in NOT_FIRMWARE:
        if not (blobs_dir / missing).exists():
            problems.append(f"{missing}: missing from app/blobs")

    # The default the UI offers must be the newest of its kind.
    for kind in (fb.KIND_GATEWAY, fb.KIND_MODULE_FACTORY, fb.KIND_MODULE_OTA):
        of_kind = [i for i in fb.IMAGES if i.kind == kind]
        if not of_kind:
            problems.append(f"{kind}: no image of this kind is bundled")
            continue
        newest = max(of_kind, key=lambda i: _ver(i.version))
        if of_kind[0] is not newest:
            problems.append(
                f"{kind}: the UI would default to {of_kind[0].version} but "
                f"{newest.version} is bundled and newer -- IMAGES must be "
                f"ordered newest-first")

    for p in problems:
        print(f"  {p}")
    if problems:
        print(f"\n{len(problems)} problem(s)")
        return 1
    kinds = {k: max((i for i in fb.IMAGES if i.kind == k),
                    key=lambda i: _ver(i.version)).version
             for k in (fb.KIND_GATEWAY, fb.KIND_MODULE_FACTORY, fb.KIND_MODULE_OTA)}
    print(f"OK - {len(fb.IMAGES)} images verified; defaults: "
          + ", ".join(f"{k}={v}" for k, v in kinds.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
