#!/usr/bin/env bash
set -euo pipefail

# Usage: ./install_protoc.sh <version> <install_prefix>
# Example: ./install_protoc.sh 28.3 ./local_deps/protoc

VERSION="${1:-}"
INSTALL_PREFIX="${2:-}"

if [[ -z "$VERSION" || -z "$INSTALL_PREFIX" ]]; then
  echo "Usage: $0 <protoc_version> <install_prefix>" >&2
  echo "Example: $0 28.3 ./local_deps/protoc" >&2
  exit 1
fi

# realpath fallback (macOS doesn't ship realpath by default)
realpath_fallback() {
  local target="$1"
  if command -v realpath >/dev/null 2>&1; then
    realpath "$target"
  else
    # POSIX compliant: cd into the directory and print $PWD
    (
      cd "$(dirname "$target")"
      printf "%s/%s\n" "$(pwd -P)" "$(basename "$target")"
    )
  fi
}

# Resolve absolute paths
INSTALL_PREFIX_ABS="$(realpath_fallback "$INSTALL_PREFIX")"

# Detect OS
uname_s="$(uname -s)"
case "$uname_s" in
  Linux)  OS="linux" ;;
  Darwin) OS="osx" ;;
  *)
    echo "Unsupported OS: $uname_s (only Linux and macOS supported)" >&2
    exit 1
    ;;
esac

# Detect ARCH
uname_m="$(uname -m)"
case "$uname_m" in
  x86_64|amd64) ARCH="x86_64" ;;
  arm64|aarch64) ARCH="aarch_64" ;;
  *)
    echo "Unsupported architecture: $uname_m (only amd64/x86_64 or arm64/aarch64 supported)" >&2
    exit 1
    ;;
esac

# Construct URL
BASE_URL="https://github.com/protocolbuffers/protobuf/releases/download"
FILE="protoc-${VERSION}-${OS}-${ARCH}.zip"
URL="${BASE_URL}/v${VERSION}/${FILE}"

echo "Detected OS:        $OS"
echo "Detected ARCH:      $ARCH"
echo "protoc version:     $VERSION"
echo "Download URL:       $URL"
echo "Install prefix (abs): $INSTALL_PREFIX_ABS"
echo

# Ensure curl exists
if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required but not installed." >&2
  exit 1
fi

# Create and resolve temp dir
TMPDIR="$(mktemp -d)"
TMPDIR_ABS="$(realpath_fallback "$TMPDIR")"
cleanup() { rm -rf "$TMPDIR_ABS"; }
trap cleanup EXIT

cd "$TMPDIR_ABS"

echo "Temp directory:     $TMPDIR_ABS"
echo

# Download
echo "Downloading with curl..."
curl -fL "$URL" -o "$FILE"

# Extract
unzip -o "$FILE" >/dev/null

# Install locally
BIN_DIR="${INSTALL_PREFIX_ABS}/bin"
INCLUDE_DIR="${INSTALL_PREFIX_ABS}/include"

echo "Installing to:"
echo "  Binary directory:  $BIN_DIR"
echo "  Include directory: $INCLUDE_DIR"
echo

mkdir -p "$BIN_DIR" "$INCLUDE_DIR"

cp -f bin/protoc "$BIN_DIR/"
cp -rf include/* "$INCLUDE_DIR/"

PROTOC_BIN="${BIN_DIR}/protoc"

echo
echo "protoc ${VERSION} installed successfully!"
echo "Protoc binary:  $PROTOC_BIN"
echo "Protoc version: $("$PROTOC_BIN" --version)"
echo
echo "Add this to your PATH:"
echo "  export PATH=\"${BIN_DIR}:\$PATH\""
