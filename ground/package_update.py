import hashlib
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


# This script is intended to be run from the ground/ directory.
PRIVATE_KEY = Path("keys/ground.key.pem")

# Use the identifier for your actual device.
TARGET_ID = "raspberry-pi-zero-w"
APPLICATION_ID = "pqc-rescue-app"
KEY_ID = "ground-key-1"
OUTPUT_PACKAGE = Path("update.tar.gz")


if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} payload-file version")
    sys.exit(1)


payload = Path(sys.argv[1])
version = sys.argv[2]

if not payload.is_file():
    raise SystemExit(f"Payload not found: {payload}")

if not PRIVATE_KEY.is_file():
    raise SystemExit(f"Private key not found: {PRIVATE_KEY}")


payload_name = payload.name
payload_path = f"payload/{payload_name}"

payload_data = payload.read_bytes()
payload_size = len(payload_data)
payload_sha256 = hashlib.sha256(payload_data).hexdigest()


# This manifest is signed.
manifest = {
    "manifest_version": 1,
    "target_id": TARGET_ID,
    "application_id": APPLICATION_ID,
    "version": version,
    "key_id": KEY_ID,
    "entrypoint": payload_path,
    "image_size": payload_size,
    "image_sha256": payload_sha256,
}


with tempfile.TemporaryDirectory() as temporary_directory:
    temporary_directory = Path(temporary_directory)

    manifest_path = temporary_directory / "manifest.json"
    signature_path = temporary_directory / "manifest.sig"

    # Use deterministic JSON formatting so the signed bytes are predictable.
    manifest_path.write_text(
        json.dumps(
            manifest,
            sort_keys=True,
            separators=(",", ":"),
        ) + "\n",
        encoding="utf-8",
    )

    # Sign the finalized manifest using ML-DSA-65.
    subprocess.run(
        [
            "openssl",
            "pkeyutl",
            "-sign",
            "-in",
            str(manifest_path),
            "-inkey",
            str(PRIVATE_KEY),
            "-out",
            str(signature_path),
        ],
        check=True,
    )

    # Put the manifest, signature, and payload into one package.
    with tarfile.open(OUTPUT_PACKAGE, "w:gz") as package:
        package.add(
            manifest_path,
            arcname="manifest.json",
        )

        package.add(
            signature_path,
            arcname="manifest.sig",
        )

        package.add(
            payload,
            arcname=payload_path,
        )


print(f"Created {OUTPUT_PACKAGE}")
print(f"Version: {version}")
print(f"Target: {TARGET_ID}")
print(f"Payload: {payload_path}")
print(f"Size: {payload_size} bytes")
print(f"SHA-256: {payload_sha256}")
