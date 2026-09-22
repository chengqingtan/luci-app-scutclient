#!/usr/bin/env bash
# Run in Linux; the SDK contains Linux x86_64 host tools.
set -euo pipefail

if [[ $# != 4 ]]; then
    echo "Usage: bash scripts/build-packages.sh RELEASE ARCH EMPTY_WORK_DIR EMPTY_OUTPUT_DIR" >&2
    exit 2
fi
if [[ $(uname -s) != Linux || $(uname -m) != x86_64 ]]; then
    echo "This SDK requires Linux x86_64 (for example Ubuntu in WSL2)." >&2
    exit 2
fi
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
release=$1
arch=$2
sdk_url=$(python3 "$source_dir/scripts/sdk_matrix.py" "$release" "$arch" --field url)
sdk_sha=$(python3 "$source_dir/scripts/sdk_matrix.py" "$release" "$arch" --field sha256)
package_format=$(python3 "$source_dir/scripts/sdk_matrix.py" "$release" "$arch" --field format)

# Never delete an existing SDK or mix stale packages into a new build.
for directory in "$3" "$4"; do
    if [[ -e "$directory" ]]; then
        echo "Directory already exists; choose a fresh path: $directory" >&2
        exit 2
    fi
done
mkdir -p -- "$3" "$4"
work_dir=$(cd -- "$3" && pwd)
output_dir=$(cd -- "$4" && pwd)
export LC_ALL=C TZ=UTC

echo "Building ImmortalWrt $release / $arch ($package_format)"
curl --fail --location --retry 3 --connect-timeout 30 --output "$work_dir/sdk.tar.zst" "$sdk_url"
echo "$sdk_sha  $work_dir/sdk.tar.zst" | sha256sum --check --strict
mkdir "$work_dir/sdk"
tar --zstd -xf "$work_dir/sdk.tar.zst" -C "$work_dir/sdk" --strip-components=1
cd "$work_dir/sdk"

# Preserve release SDK feed URLs and revision pins, including the base feed.
test -f feeds.conf.default
./scripts/feeds update -a
./scripts/feeds install -a
test -f feeds/luci/luci.mk
test -f package/feeds/packages/scutclient/Makefile

# The only active LuCI package entry must refer to this checkout.
while IFS= read -r -d '' entry; do
    if [[ ! -L "$entry" ]]; then
        echo "Refusing to overwrite a real package directory: $entry" >&2
        exit 1
    fi
    unlink "$entry"
done < <(find package/feeds -mindepth 2 -maxdepth 2 -name luci-app-scutclient -print0)
test ! -e package/luci-app-scutclient
mkdir package/luci-app-scutclient
for entry in Makefile luasrc root htdocs src po ucode patches; do
    if [[ -e "$source_dir/$entry" ]]; then
        cp -a "$source_dir/$entry" package/luci-app-scutclient/
    fi
done
diff -r "$source_dir/luasrc" package/luci-app-scutclient/luasrc
diff -r "$source_dir/root" package/luci-app-scutclient/root

cat > .config <<'EOF'
CONFIG_ALL=n
CONFIG_ALL_KMODS=n
CONFIG_ALL_NONSHARED=n
CONFIG_AUTOREMOVE=n
CONFIG_SIGNED_PACKAGES=n
CONFIG_LUCI_SRCDIET=n
CONFIG_LUCI_JSMIN=n
CONFIG_LUCI_CSSTIDY=n
CONFIG_PACKAGE_scutclient=m
CONFIG_PACKAGE_luci-app-scutclient=m
EOF
make defconfig
grep -qx "CONFIG_TARGET_ARCH_PACKAGES=\"$arch\"" .config
grep -qxE 'CONFIG_PACKAGE_scutclient=[my]' .config
grep -qxE 'CONFIG_PACKAGE_luci-app-scutclient=[my]' .config
if [[ "$package_format" == apk ]]; then
    grep -qx 'CONFIG_USE_APK=y' .config
elif grep -qx 'CONFIG_USE_APK=y' .config; then
    echo "SDK uses APK but manifest expects IPK" >&2
    exit 1
fi

# Separate targets avoid concurrent dependency builds writing to the same SDK.
jobs=$(nproc)
for target in package/feeds/packages/scutclient/compile package/luci-app-scutclient/compile; do
    if ! make "$target" -j"$jobs" V=s; then
        echo "Parallel build failed; retrying once with a serial diagnostic log."
        make "$target" -j1 V=s
    fi
done

python3 "$source_dir/scripts/verify_packages.py" \
    --sdk "$work_dir/sdk" --source "$source_dir" \
    --release "$release" --arch "$arch" --output "$output_dir/packages"
echo "Verified packages: $output_dir/packages"
