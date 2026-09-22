"""Offline regression checks for SDK selection and artifact acceptance."""
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sdk_matrix import load_manifest, matrix
from verify_packages import collect, package_version, read_ipk, validate_metadata, validate_payload, ELF_TARGETS


def archive(files):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as tar:
        for name, content in files.items():
            entry = tarfile.TarInfo(name)
            entry.size = len(content)
            tar.addfile(entry, io.BytesIO(content))
    return stream.getvalue()


class BuildToolsTest(unittest.TestCase):
    def test_every_supported_combination(self):
        for release, config in load_manifest().items():
            rows = matrix(release, "all")["include"]
            self.assertEqual(len(rows), 5)
            self.assertEqual({row["arch"] for row in rows}, set(ELF_TARGETS))
            for row in rows:
                self.assertEqual(matrix(release, row["arch"])["include"], [row])
                self.assertEqual(row["format"], config["format"])
                self.assertIn(f"/{row['release']}/targets/{row['target']}/", row["url"])
                self.assertTrue(row["url"].startswith(f"https://downloads.{row['distribution']}.org/"))
                self.assertTrue(row["filename"].startswith(f"{row['system'].split('-')[0]}-sdk-{row['release']}-"))
        self.assertEqual(matrix("25.12.2", "aarch64_cortex-a53")["include"][0]["format"], "apk")
        self.assertEqual(matrix("24.10.6", "aarch64_cortex-a53")["include"][0]["format"], "ipk")
        self.assertEqual(matrix("openwrt-25.12.5", "x86_64")["include"][0]["format"], "apk")
        self.assertEqual(matrix("openwrt-24.10.8", "x86_64")["include"][0]["format"], "ipk")

    def test_legacy_versions_still_select_immortalwrt(self):
        for version in ("25.12.2", "24.10.6"):
            self.assertEqual(matrix(version, "all"), matrix(f"immortalwrt-{version}", "all"))

    def test_unknown_inputs_fail_before_download(self):
        for release, arch in (("snapshot", "x86_64"), ("25.12.2", "arm64"), ("25.12.2", "../all"),
                              ("openwrt-25.12.2", "x86_64"), ("immortalwrt-25.12.5", "x86_64"),
                              ("25.12.5", "x86_64")):
            with self.assertRaises(ValueError):
                matrix(release, arch)

    def test_ipk_control_and_payload(self):
        control = b"Package: scutclient\nVersion: 3.1.3-r1\nArchitecture: mips_24kc\nDepends: libc\n"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sample.ipk"
            path.write_bytes(archive({
                "./debian-binary": b"2.0\n",
                "./control.tar.gz": archive({"./control": control}),
                "./data.tar.gz": archive({"./usr/bin/scutclient": b"sample"}),
            }))
            metadata, payload = read_ipk(path)
            validate_metadata(metadata, "scutclient", "3.1.3-r1", "mips_24kc")
            self.assertEqual(payload["usr/bin/scutclient"], b"sample")
            with self.assertRaises(ValueError):
                validate_metadata(metadata, "scutclient", "3.1.3-r1", "mipsel_24kc")

    def test_luci_metadata_rejects_wrong_version_or_missing_dependencies(self):
        metadata = dict(name="luci-app-scutclient", version="26.264.1-r1", arch="all",
                        depends=["scutclient", "luci-compat", "luci-lib-nixio", "luci-lua-runtime"])
        validate_metadata(metadata, metadata["name"], metadata["version"], "x86_64")
        with self.assertRaises(ValueError):
            validate_metadata(metadata, metadata["name"], "old-version", "x86_64")
        metadata["depends"] = metadata["depends"][:-1]
        with self.assertRaises(ValueError):
            validate_metadata(metadata, metadata["name"], metadata["version"], "x86_64")

    def test_elf_endianness_is_checked(self):
        for arch, (machine, elf_class, endian) in ELF_TARGETS.items():
            header = bytearray(64)
            header[:6] = b"\x7fELF" + bytes([elf_class, endian])
            header[18:20] = machine.to_bytes(2, "little" if endian == 1 else "big")
            payload = {"usr/bin/scutclient": bytes(header), "etc/init.d/scutclient": b"init",
                       "etc/config/scutclient": b"config"}
            validate_payload("scutclient", payload, ROOT, arch)
            header[5] = 2 if endian == 1 else 1
            payload["usr/bin/scutclient"] = bytes(header)
            with self.assertRaises(ValueError):
                validate_payload("scutclient", payload, ROOT, arch)

    def test_original_luci_cannot_replace_custom_luci(self):
        payload = {}
        for directory, prefix in (("root", ""), ("luasrc", "usr/lib/lua/luci/")):
            payload.update({prefix + file.relative_to(ROOT / directory).as_posix(): file.read_bytes()
                            for file in (ROOT / directory).rglob("*") if file.is_file()})
        validate_payload("luci-app-scutclient", payload, ROOT, "aarch64_cortex-a53")
        payload["usr/lib/lua/luci/view/scutclient/logs.htm"] = b"old XHR logs page"
        with self.assertRaises(ValueError):
            validate_payload("luci-app-scutclient", payload, ROOT, "aarch64_cortex-a53")

    def test_source_json_is_valid(self):
        for file in (ROOT / "root").rglob("*.json"):
            json.loads(file.read_text(encoding="utf-8"))

    def test_collect_uses_selected_core_recipe_and_unique_raw_outputs(self):
        # Both formats and both core recipe locations; the APK reader is mocked
        # because the SDK's Linux host executable cannot run in Windows tests.
        luci_payload = {}
        for directory, prefix in (("root", ""), ("luasrc", "usr/lib/lua/luci/")):
            luci_payload.update({prefix + file.relative_to(ROOT / directory).as_posix(): file.read_bytes()
                                 for file in (ROOT / directory).rglob("*") if file.is_file()})
        luci_version = package_version(ROOT / "Makefile")
        names = set()
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for system in load_manifest():
                for row in matrix(system, "all")["include"]:
                    arch = row["arch"]
                    sdk = base / system / arch / "sdk"
                    recipes = sdk / row["core_package_dir"]
                    recipes.mkdir(parents=True)
                    # Different fixture versions catch reading the wrong recipe.
                    core_release = "2" if row["distribution"] == "openwrt" else "1"
                    (recipes / "Makefile").write_text(f"PKG_VERSION:=3.1.3\nPKG_RELEASE:={core_release}\n")
                    machine, elf_class, endian = ELF_TARGETS[arch]
                    header = bytearray(64)
                    header[:6] = b"\x7fELF" + bytes([elf_class, endian])
                    header[18:20] = machine.to_bytes(2, "little" if endian == 1 else "big")
                    core_payload = {"usr/bin/scutclient": bytes(header), "etc/init.d/scutclient": b"init",
                                    "etc/config/scutclient": b"config"}
                    package_dir = sdk / "bin/packages"
                    package_dir.mkdir(parents=True)
                    decoded = {}
                    for name, version, package_arch, payload in (
                        ("scutclient", f"3.1.3-r{core_release}", arch, core_payload),
                        ("luci-app-scutclient", luci_version, "all", luci_payload),
                    ):
                        depends = ["scutclient", "luci-compat", "luci-lib-nixio", "luci-lua-runtime"] if name.startswith("luci-") else ["libc"]
                        metadata = dict(name=name, version=version, arch=package_arch, depends=depends)
                        if row["format"] == "ipk":
                            path = package_dir / f"{name}_{version}_{package_arch}.ipk"
                            control = f"Package: {name}\nVersion: {version}\nArchitecture: {package_arch}\nDepends: {', '.join(depends)}\n"
                            path.write_bytes(archive({"control.tar.gz": archive({"control": control.encode()}),
                                                      "data.tar.gz": archive(payload)}))
                        else:
                            path = package_dir / f"{name}-{version}.apk"
                            path.write_bytes(b"fixture APK")
                        decoded[path.name] = (metadata, payload)
                    output = sdk.parent / "output"
                    github_output = sdk.parent / "github-output"
                    with patch("verify_packages.read_apk", side_effect=lambda path, sdk: decoded[path.name]), \
                            patch.dict(os.environ, {"GITHUB_OUTPUT": str(github_output)}), \
                            patch("builtins.print"):
                        collect(sdk, ROOT, system, arch, output)
                    files = list(output.iterdir())
                    self.assertEqual(len(files), 2)
                    for file in files:
                        self.assertTrue(file.name.endswith(f"-{system}-{arch}.{row['format']}"))
                        self.assertNotIn(file.name, names)
                        names.add(file.name)
                    values = dict(line.split("=", 1) for line in github_output.read_text().splitlines())
                    self.assertEqual(set(values), {"core_package", "luci_package"})
                    self.assertEqual({Path(path) for path in values.values()}, set(files))
        self.assertEqual(len(names), 40)


if __name__ == "__main__":
    unittest.main()
