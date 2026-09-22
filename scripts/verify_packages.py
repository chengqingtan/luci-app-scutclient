#!/usr/bin/env python3
"""Inspect package metadata and payloads before publishing CI artifacts."""

import argparse
from datetime import datetime, timezone
from email.parser import Parser
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile

from sdk_matrix import matrix

PACKAGES = ("scutclient", "luci-app-scutclient")
LUCI_DEPENDENCIES = {"scutclient", "luci-compat", "luci-lib-nixio", "luci-lua-runtime"}
# ELF e_machine, EI_CLASS, EI_DATA. This catches host binaries and MIPS endian mixups.
ELF_TARGETS = {
    "aarch64_cortex-a53": (183, 2, 1),
    "aarch64_generic": (183, 2, 1),
    "x86_64": (62, 2, 1),
    "mipsel_24kc": (8, 1, 1),
    "mips_24kc": (8, 1, 2),
}


def run(*args):
    return subprocess.check_output([str(arg) for arg in args], text=True).strip()


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def make_value(path, key):
    match = re.search(rf"^{re.escape(key)}\s*:?=\s*(\S+)\s*$", path.read_text(), re.MULTILINE)
    if not match:
        raise ValueError(f"Missing {key} in {path}")
    return match[1]


def package_version(makefile):
    return f"{make_value(makefile, 'PKG_VERSION')}-r{make_value(makefile, 'PKG_RELEASE')}"


def tar_files(data):
    """Read regular files without extracting arbitrary archive paths to disk."""
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as archive:
        return {
            entry.name.removeprefix("./"): archive.extractfile(entry).read()
            for entry in archive if entry.isfile()
        }


def read_ipk(path):
    if path.read_bytes()[:8] == b"!<arch>\n":
        # Some opkg producers use ar; ImmortalWrt ipkg-build uses a tar envelope.
        names = run("ar", "t", path).splitlines()
        parts = {name: subprocess.check_output(["ar", "p", str(path), name]) for name in names}
    else:
        parts = tar_files(path.read_bytes())
    controls = [value for name, value in parts.items() if name.startswith("control.tar")]
    payloads = [value for name, value in parts.items() if name.startswith("data.tar")]
    if len(controls) != 1 or len(payloads) != 1:
        raise ValueError(f"Invalid IPK envelope: {path}")
    control = Parser().parsestr(tar_files(controls[0])["control"].decode())
    metadata = {
        "name": control["Package"], "version": control["Version"],
        "arch": control["Architecture"],
        "depends": [dep.strip() for dep in (control["Depends"] or "").split(",") if dep.strip()],
    }
    return metadata, tar_files(payloads[0])


def read_apk(path, sdk):
    apk = sdk / "staging_dir/host/bin/apk"
    metadata = json.loads(run(apk, "adbdump", "--format", "json", path))["info"]
    with tempfile.TemporaryDirectory(prefix="scutclient-apk-") as temp:
        # extract never installs packages or runs package maintainer scripts.
        run(apk, "extract", "--allow-untrusted", "--no-chown", "--destination", temp, path)
        root = Path(temp)
        payload = {file.relative_to(root).as_posix(): file.read_bytes()
                   for file in root.rglob("*") if file.is_file() and not file.is_symlink()}
    return metadata, payload


def validate_metadata(metadata, name, version, arch):
    if metadata.get("name") != name or metadata.get("version") != version:
        raise ValueError(f"Unexpected name/version for {name}: {metadata}")
    expected_arches = {arch} if name == "scutclient" else {"all", "noarch", arch}
    if metadata.get("arch") not in expected_arches:
        raise ValueError(f"Unexpected architecture for {name}: {metadata.get('arch')}")
    if name == "luci-app-scutclient":
        # adbdump versions may serialize dependencies as strings or objects.
        depends = {re.split(r"[\s<>=~]", dep if isinstance(dep, str) else dep["name"])[0]
                   for dep in metadata.get("depends", [])}
        if missing := LUCI_DEPENDENCIES - depends:
            raise ValueError(f"Missing LuCI runtime dependencies: {sorted(missing)}")


def validate_payload(name, payload, source, arch):
    if name == "scutclient":
        binary = payload.get("usr/bin/scutclient", b"")
        if len(binary) < 20 or binary[:4] != b"\x7fELF":
            raise ValueError("scutclient executable is missing or not ELF")
        endian = "little" if binary[5] == 1 else "big"
        actual = (int.from_bytes(binary[18:20], endian), binary[4], binary[5])
        if actual != ELF_TARGETS[arch]:
            raise ValueError(f"Wrong scutclient ELF architecture: {actual}")
        for path in ("etc/init.d/scutclient", "etc/config/scutclient"):
            if not payload.get(path):
                raise ValueError(f"Missing core package file: {path}")
    else:
        # Minification is disabled for this build, allowing exact source checks.
        for directory, prefix in (("luasrc", "usr/lib/lua/luci/"), ("root", "")):
            for file in (source / directory).rglob("*"):
                if not file.is_file():
                    continue
                target = prefix + file.relative_to(source / directory).as_posix()
                if payload.get(target) != file.read_bytes():
                    raise ValueError(f"Package differs from this checkout: {target}")


def collect(sdk, source, release, arch, output):
    selection = matrix(release, arch)["include"][0]
    if output.exists():
        raise ValueError(f"Output already exists: {output}")
    verified = []
    for name in PACKAGES:
        pattern = f"{name}_*.ipk" if selection["format"] == "ipk" else f"{name}-[0-9]*.apk"
        candidates = list((sdk / "bin/packages").rglob(pattern))
        if len(candidates) != 1:
            raise ValueError(f"Expected one {name} package, found {len(candidates)}: {candidates}")
        package = candidates[0]
        makefile = source / "Makefile" if name.startswith("luci-") else sdk / "feeds/packages/net/scutclient/Makefile"
        metadata, payload = read_ipk(package) if selection["format"] == "ipk" else read_apk(package, sdk)
        validate_metadata(metadata, name, package_version(makefile), arch)
        validate_payload(name, payload, source, arch)
        verified.append((package, metadata))

    # Do not create the artifact directory until BOTH packages pass verification.
    output.mkdir(parents=True)
    for package, _ in verified:
        shutil.copy2(package, output / package.name)
    feeds = {feed.name: run("git", "-C", feed, "rev-parse", "HEAD")
             for feed in (sdk / "feeds").iterdir() if (feed / ".git").exists()}
    buildinfo = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "repository_commit": run("git", "-C", source, "rev-parse", "HEAD"),
        "repository_dirty": bool(run("git", "-C", source, "status", "--porcelain")),
        "sdk": selection, "feeds": feeds,
        "packages": [{"file": package.name, "sha256": sha256(package), "metadata": metadata}
                     for package, metadata in verified],
    }
    (output / "build-info.json").write_text(json.dumps(buildinfo, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(source / "docs/BUILD.md", output / "INSTALL.md")
    (output / "SHA256SUMS").write_text(
        "".join(f"{sha256(file)}  {file.name}\n" for file in sorted(output.iterdir()) if file.is_file()),
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("sdk", "source", "output"):
        parser.add_argument(f"--{option}", type=Path, required=True)
    for option in ("release", "arch"):
        parser.add_argument(f"--{option}", required=True)
    args = parser.parse_args()
    collect(args.sdk.resolve(), args.source.resolve(), args.release, args.arch, args.output.resolve())


if __name__ == "__main__":
    main()
