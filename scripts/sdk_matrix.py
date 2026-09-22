#!/usr/bin/env python3
"""Resolve allowlisted SDKs. Uses only the Python standard library."""

import argparse
import json
from pathlib import Path
import re

MANIFEST = Path(__file__).with_name("sdks.json")
DISTRIBUTIONS = {"immortalwrt": "ImmortalWrt", "openwrt": "OpenWrt"}
# Keep the original local CLI invocations working, without guessing a distro.
LEGACY_RELEASES = {version: f"immortalwrt-{version}" for version in ("25.12.2", "24.10.6")}


def load_manifest():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for release, config in manifest.items():
        if not re.fullmatch(r"(immortalwrt|openwrt)-\d+\.\d+\.\d+", release):
            raise ValueError(f"Invalid release: {release}")
        if config["format"] not in ("ipk", "apk"):
            raise ValueError("Invalid package format")
        for key, allowed in (
            ("compression", {"xz", "zst"}),
            ("version_style", {"revision", "revision-r"}),
            ("runner", {"ubuntu-22.04", "ubuntu-24.04"}),
            ("luci_runtime", {"builtin", "split"}),
        ):
            if config.get(key) not in allowed:
                raise ValueError(f"Invalid SDK {key}")
        if not re.fullmatch(r"\d+\.\d+\.\d+", config["gcc"]):
            raise ValueError("Invalid GCC version")
        for arch, target in config["targets"].items():
            if not re.fullmatch(r"[a-z0-9_-]+", arch) or arch == "all":
                raise ValueError(f"Invalid architecture: {arch}")
            if not re.fullmatch(r"[a-z0-9_-]+/[a-z0-9_-]+", target["target"]):
                raise ValueError("Invalid target/subtarget")
            if not re.fullmatch(r"[0-9a-f]{64}", target["sha256"]):
                raise ValueError("Missing or invalid SDK SHA256")
    return manifest


def matrix(release, architecture):
    manifest = load_manifest()
    release = LEGACY_RELEASES.get(release, release)
    if release not in manifest:
        raise ValueError(f"Unsupported release: {release}")
    config = manifest[release]
    distribution, version = release.split("-", 1)
    architectures = list(config["targets"]) if architecture == "all" else [architecture]
    rows = []
    for arch in architectures:
        if arch not in config["targets"]:
            raise ValueError(f"Unsupported architecture: {arch}")
        target = config["targets"][arch]
        filename = (
            f"{distribution}-sdk-{version}-{target['target'].replace('/', '-')}_"
            f"gcc-{config['gcc']}_musl.Linux-x86_64.tar.{config['compression']}"
        )
        rows.append(dict(
            system=release, distribution=distribution, release=version,
            label=f"{DISTRIBUTIONS[distribution]} {version}",
            arch=arch, format=config["format"],
            compression=config["compression"], version_style=config["version_style"],
            runner=config["runner"], luci_runtime=config["luci_runtime"],
            core_package_dir=("package/scutclient" if distribution == "openwrt"
                              else "package/feeds/packages/scutclient"),
            target=target["target"], sha256=target["sha256"], filename=filename,
            url=f"https://downloads.{distribution}.org/releases/{version}/targets/{target['target']}/{filename}",
        ))
    return {"include": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release", help="System selector, e.g. openwrt-25.12.5")
    parser.add_argument("architecture")
    parser.add_argument("--field", choices=("url", "sha256", "format", "arch", "target",
                                          "system", "distribution", "release", "label", "core_package_dir",
                                          "compression", "version_style", "runner", "luci_runtime"))
    args = parser.parse_args()
    try:
        result = matrix(args.release, args.architecture)
        if args.field:
            if len(result["include"]) != 1:
                raise ValueError("--field requires one architecture")
            print(result["include"][0][args.field])
        else:
            print(json.dumps(result, separators=(",", ":")))
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
