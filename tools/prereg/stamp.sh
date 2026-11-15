#!/usr/bin/env bash
# Timestamp one file with two RFC 3161 authorities and OpenTimestamps, then verify the tokens.
#
# Usage: tools/prereg/stamp.sh <file> <proof-dir>
# Needs: openssl (3.x), curl, and the OpenTimestamps client as $OTS (default: ots).
#
# Only the file's SHA-256 leaves the machine. Outputs in <proof-dir>, named after the file:
#   <name>.<tsa>.tsq / .tsr   RFC 3161 query and signed response
#   <name>.<tsa>.verify.txt   openssl verification output
#   <name>.ots                OpenTimestamps proof (pending until a Bitcoin block confirms it;
#                             run `ots upgrade <name>.ots` a few hours later)
#   <name>.<tsa>.chain.pem    certificates carried in the token
#   <name>.freetsa.ca.pem     FreeTSA's root (DigiCert verifies against public roots)
set -euo pipefail

file=$1
out=$2
OTS=${OTS:-ots}
name=$(basename "$file")
mkdir -p "$out"
ca_bundle=$(openssl version -d | sed 's/.*"\(.*\)"/\1/')/certs/ca-bundle.crt
[ -f "$ca_bundle" ] || ca_bundle=/mingw64/etc/ssl/certs/ca-bundle.crt

declare -A url=(
  [freetsa]="https://freetsa.org/tsr"
  [digicert]="http://timestamp.digicert.com"
)

for tsa in freetsa digicert; do
  q="$out/$name.$tsa.tsq"
  r="$out/$name.$tsa.tsr"
  openssl ts -query -data "$file" -sha256 -cert -out "$q"
  curl -sSf --retry 3 -H "Content-Type: application/timestamp-query" --data-binary "@$q" "${url[$tsa]}" -o "$r"
  # Certificates to verify against: FreeTSA publishes its own root; DigiCert chains to a public root.
  if [ "$tsa" = freetsa ]; then
    ca="$out/$name.$tsa.ca.pem"
    curl -sSf https://freetsa.org/files/cacert.pem -o "$ca"
  else
    ca=$ca_bundle  # the system's public roots; not copied into the proofs
  fi
  # Certificates carried inside the token serve as untrusted intermediates.
  inter="$out/$name.$tsa.chain.pem"
  openssl ts -reply -in "$r" -token_out -out "$out/.token.der"
  openssl pkcs7 -inform DER -in "$out/.token.der" -print_certs -out "$inter"
  rm -f "$out/.token.der"
  {
    openssl ts -verify -in "$r" -queryfile "$q" -CAfile "$ca" -untrusted "$inter"
    openssl ts -reply -in "$r" -text | grep -E "Time stamp|Hash Algorithm|Message data|Serial|TSA|Policy"
  } >"$out/$name.$tsa.verify.txt" 2>&1
  grep -q "Verification: OK" "$out/$name.$tsa.verify.txt" || { cat "$out/$name.$tsa.verify.txt"; exit 1; }
  echo "$tsa: $(grep 'Time stamp:' "$out/$name.$tsa.verify.txt")"
done

cp "$file" "$out/.ots-input"
"$OTS" stamp "$out/.ots-input"
mv "$out/.ots-input.ots" "$out/$name.ots"
rm -f "$out/.ots-input"
"$OTS" info "$out/$name.ots" | head -5
echo "sha256 $(sha256sum "$file" | cut -d' ' -f1)  $name"
