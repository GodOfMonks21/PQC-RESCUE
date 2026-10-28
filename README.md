# PQC RESCUE

Prototype for creating, sending, verifying, and staging signed application updates.

## Setup

The ground laptop needs the ML-DSA-65 private signing key. Put it here:

```text
ground/keys/ground.key.pem
```

The ground laptop also needs the SSH private key used to connect to the Pi:

```text
~/.ssh/pqc_rescue_pi_ssh
```

These private keys are not included in this repository. Obtain them separately and never commit them to Git.

## Basic workflow
The package update script takes two arguments: `payload`, `file version`.
From the `ground` directory, create an update:

```bash
python3 package_update.py ./payload/payload.bin 1
```

This creates `update.tar.gz` with includes the payload, manifest, and ML-DSA-65 signature.
Send it to the Pi:

```bash
./send_update.sh update.tar.gz
```

The script uploads the package to this specific location on the Pi:
`/var/lib/pqc-rescue/incoming/update.tar.gz`.

On the Pi, process the received update:

```bash
python3 process_update.py /var/lib/pqc-rescue/incoming/update.tar.gz
```

The update is verified and staged before it can be activated.
