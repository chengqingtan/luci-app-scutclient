"""Offline regression checks for SDK selection and artifact acceptance."""
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sdk_matrix import load_manifest, matrix
from verify_packages import read_ipk, validate_metadata, validate_payload, ELF_TARGETS


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
                self.assertIn(f"/{release}/targets/{row['target']}/", row["url"])
        self.assertEqual(matrix("25.12.2", "aarch64_cortex-a53")["include"][0]["format"], "apk")
        self.assertEqual(matrix("24.10.6", "aarch64_cortex-a53")["include"][0]["format"], "ipk")

    def test_unknown_inputs_fail_before_download(self):
        for release, arch in (("snapshot", "x86_64"), ("25.12.2", "arm64"), ("25.12.2", "../all")):
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


if __name__ == "__main__":
    unittest.main()
