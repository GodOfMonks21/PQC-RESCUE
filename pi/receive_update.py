#!/usr/bin/env python3

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


PUBLIC_KEY = Path("keys/ground.pub.pem")

EXPECTED_TARGET = "raspberry-pi-zero-w"
EXPECTED_KEY_ID = "ground-key-1"

STAGING_ROOT = Path.home() / "pqc-rescue" / "staged"


if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} /path/to/update.tar.gz")
    sys.exit(1)


package_path = Path(sys.argv[1]).resolve()

if not package_path.is_file():
    raise SystemExit(f"Package not found: {package_path}")

if not PUBLIC_KEY.is_file():
    raise SystemExit(f"Public key not found: {PUBLIC_KEY}")


with tempfile.TemporaryDirectory() as temporary_directory:
    extraction_directory = Path(temporary_directory)

    with tarfile.open(package_path, "r:gz") as package:
        members = package.getmembers()
        names = set()

        for member in members:
            if member.name in names:
                raise SystemExit(
                    f"Duplicate package entry: {member.name}"
                )

            names.add(member.name)

            if not member.isfile():
                raise SystemExit(
                    f"Package contains a non-file entry: {member.name}"
                )

            destination = (
                extraction_directory / member.name
            ).resolve()

            if extraction_directory not in destination.parents:
                raise SystemExit(
                    f"Unsafe package path: {member.name}"
                )

        package.extractall(
            extraction_directory,
            filter="data",
        )

    manifest_path = extraction_directory / "manifest.json"
    signature_path = extraction_directory / "manifest.sig"

    if not manifest_path.is_file():
        raise SystemExit("Package is missing manifest.json")

    if not signature_path.is_file():
        raise SystemExit("Package is missing manifest.sig")

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    required_fields = {
        "manifest_version",
        "target_id",
        "application_id",
        "version",
        "key_id",
        "entrypoint",
        "image_size",
        "image_sha256",
    }

    missing_fields = required_fields - manifest.keys()

    if missing_fields:
        raise SystemExit(
            f"Manifest is missing fields: {sorted(missing_fields)}"
        )

    if manifest["target_id"] != EXPECTED_TARGET:
        raise SystemExit(
            f"Wrong target: {manifest['target_id']}"
        )

    if manifest["key_id"] != EXPECTED_KEY_ID:
        raise SystemExit(
            f"Unknown key ID: {manifest['key_id']}"
        )

    version = str(manifest["version"])

    if not re.fullmatch(r"[A-Za-z0-9._-]+", version):
        raise SystemExit(f"Unsafe version: {version}")

    print("Checking manifest signature...")

    verification = subprocess.run(
        [
            "openssl",
            "pkeyutl",
            "-verify",
            "-in",
            str(manifest_path),
            "-pubin",
            "-inkey",
            str(PUBLIC_KEY),
            "-sigfile",
            str(signature_path),
        ],
        capture_output=True,
        text=True,
    )

    if verification.returncode != 0:
        raise SystemExit(
            "Manifest signature verification failed"
        )

    entrypoint = Path(manifest["entrypoint"])

    if entrypoint.is_absolute():
        raise SystemExit(
            "Manifest entrypoint must be relative"
        )

    payload_path = (
        extraction_directory / entrypoint
    ).resolve()

    if extraction_directory not in payload_path.parents:
        raise SystemExit(
            "Unsafe manifest entrypoint"
        )

    if not payload_path.is_file():
        raise SystemExit(
            f"Payload not found: {manifest['entrypoint']}"
        )

    actual_size = payload_path.stat().st_size
    expected_size = int(manifest["image_size"])

    if actual_size != expected_size:
        raise SystemExit(
            f"Payload size mismatch: "
            f"expected {expected_size}, got {actual_size}"
        )

    actual_hash = hashlib.sha256(
        payload_path.read_bytes()
    ).hexdigest()

    if actual_hash != manifest["image_sha256"]:
        raise SystemExit("Payload SHA-256 mismatch")

    stage_directory = STAGING_ROOT / version

    if stage_directory.exists():
        raise SystemExit(
            f"Version {version} is already staged"
        )

    temporary_stage = STAGING_ROOT / f".{version}.tmp"

    temporary_stage.mkdir(
        parents=True,
        exist_ok=False,
    )

    shutil.copy2(
        payload_path,
        temporary_stage / payload_path.name,
    )

    shutil.copy2(
        manifest_path,
        temporary_stage / "manifest.json",
    )

    shutil.copy2(
        signature_path,
        temporary_stage / "manifest.sig",
    )

    temporary_stage.rename(stage_directory)


print("Update verified successfully.")
print(f"Version staged: {version}")
print(f"Location: {stage_directory}")
