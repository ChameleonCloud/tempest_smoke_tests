#!/bin/bash

# Exit on error for most commands, but we'll handle test failures gracefully
set -e

# Default values
REGEX=""
DRY_RUN=false

# Function to print usage
usage() {
    echo "Usage: $0 --config-path <path> --name <name> --accounts-passphrase <passphrase> [--regex <regex>] [--dry-run]"
    exit 1
}

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --config-path) CONFIG_PATH="$2"; shift ;;
        --name) NAME="$2"; shift ;;
        --regex) REGEX="$2"; shift ;;
        --accounts-passphrase) ACCOUNTS_PASSPHRASE="$2"; shift ;;
        --dry-run) DRY_RUN=true ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

# Validate required arguments
if [ -z "$CONFIG_PATH" ] || [ -z "$NAME" ] || [ -z "$ACCOUNTS_PASSPHRASE" ]; then
    echo "Error: Missing required arguments."
    usage
fi

echo "Starting Smoke Tests with the following configuration:"
echo "  Config Path: $CONFIG_PATH"
echo "  Name: $NAME"
echo "  Regex: $REGEX"
echo "  Dry Run: $DRY_RUN"

# 1. Install tempest if not present (simplified check)
if ! command -v tempest &> /dev/null; then
    echo "Tempest not found. Installing..."
    if [ "$DRY_RUN" = false ]; then
        pip install .
    else
        echo "[Dry Run] Would run: pip install ."
    fi
else
    echo "Tempest is already installed."
fi

# 2. Decrypt accounts file
echo "Decrypting accounts file..."
export SECRET_PASSPHRASE="$ACCOUNTS_PASSPHRASE"
if [ "$DRY_RUN" = false ]; then
    ./decrypt_secret.sh "$CONFIG_PATH/accounts.yaml.gpg" "$CONFIG_PATH/accounts.yaml"
else
    echo "[Dry Run] Would run: ./decrypt_secret.sh $CONFIG_PATH/accounts.yaml.gpg $CONFIG_PATH/accounts.yaml"
fi

# 3. Initialize workspace
echo "Initializing Tempest workspace..."
if [ "$DRY_RUN" = false ]; then
    # Remove existing workspace if it exists to ensure clean state, or just let tempest init handle/fail
    if [ -d "workspace" ]; then
        echo "Removing existing workspace..."
        rm -rf workspace
    fi
    tempest init --config-dir "$CONFIG_PATH" --name "$NAME" workspace
    
    echo "Templated config:"
    ls -al workspace/etc/
    cat workspace/etc/tempest.conf
else
    echo "[Dry Run] Would run: tempest init --config-dir $CONFIG_PATH --name $NAME workspace"
fi

# 4. List and Run Tests
if [ "$DRY_RUN" = false ]; then
    cd workspace
    
    echo "Listing tests..."
    if [[ -n "$REGEX" ]]; then
        tempest run --list-tests --regex "$REGEX"
    else
        tempest run --list-tests --include-list etc/include_list --exclude-list etc/exclude_list
    fi

    echo "Running tests..."
    set +e # Disable exit on error to capture test failures
    if [[ -n "$REGEX" ]]; then
        echo "Running tests matching regex: $REGEX"
        tempest run --concurrency 2 --regex "$REGEX"
    else
        echo "Running all tests in include_list excluding exclude_list"
        tempest run --concurrency 2 --include-list etc/include_list --exclude-list etc/exclude_list
    fi
    TEST_EXIT_CODE=$?
    set -e # Re-enable exit on error
    
    cd ..
else
    echo "[Dry Run] Would list and run tests in 'workspace' directory."
    TEST_EXIT_CODE=0
fi

# 5. Generate CTRF Report
echo "Generating CTRF report..."
if [ "$DRY_RUN" = false ]; then
    python3 src/tempest_runner/parse_results.py workspace
else
    echo "[Dry Run] Would run: python3 src/tempest_runner/parse_results.py workspace"
fi

# Exit with the code from the test run so CI knows if it failed
exit $TEST_EXIT_CODE
