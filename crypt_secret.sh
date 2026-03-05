#!/bin/sh

# Usage: crypt_secret.sh encrypt|decrypt <input> <output>
# Reads passphrase from $SECRET_PASSPHRASE

MODE="$1"
INPUT="$2"
OUTPUT="$3"

case "$MODE" in
    encrypt)
        gpg --quiet --batch --yes --symmetric --passphrase="$SECRET_PASSPHRASE" --output "$OUTPUT" "$INPUT"
        ;;
    decrypt)
        gpg --quiet --batch --yes --decrypt --passphrase="$SECRET_PASSPHRASE" --output "$OUTPUT" "$INPUT"
        ;;
    *)
        echo "Usage: $0 encrypt|decrypt <input> <output>"
        exit 1
        ;;
esac
