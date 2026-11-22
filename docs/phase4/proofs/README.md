# Timestamp proofs for the issue 2027.01 package

What is timestamped is the committed manifest of the sealed package,
`docs/phase4/package_2027.01_manifest.json`. Its SHA-256 is the package digest:

```
bc834b2691f0f1c9fdee05a0c0fbae87958efe3a8d3e670aeff113f9b02b7949
```

The manifest lists every file of the package with its size and SHA-256, so a timestamp on the
manifest is a timestamp on every layer of the forecast. Only the hash was sent to the services.

| Proof | Service | Standard | Time (UTC) |
|---|---|---|---|
| `package_2027.01_manifest.json.freetsa.tsr` | FreeTSA (freetsa.org) | RFC 3161 | 2026-11-22 08:24:35 |
| `package_2027.01_manifest.json.digicert.tsr` | DigiCert (timestamp.digicert.com) | RFC 3161 | 2026-11-22 08:24:37 |
| `package_2027.01_manifest.json.ots` | OpenTimestamps calendars, anchored in Bitcoin | OpenTimestamps | Bitcoin block 977,029, mined 2026-11-22 09:03:53 |

Each `.tsq` is the query sent; each `.chain.pem` holds the certificates carried in the token;
`freetsa.ca.pem` is FreeTSA's published root; `*.verify.txt` is the verification output at
stamping time.

## Verify

From the repository root, with OpenSSL 3:

```bash
cd docs/phase4/proofs
openssl ts -verify -data ../package_2027.01_manifest.json -in package_2027.01_manifest.json.freetsa.tsr -CAfile package_2027.01_manifest.json.freetsa.ca.pem -untrusted package_2027.01_manifest.json.freetsa.chain.pem
```

```bash
openssl ts -verify -data ../package_2027.01_manifest.json -in package_2027.01_manifest.json.digicert.tsr -CAfile /etc/ssl/certs/ca-certificates.crt -untrusted package_2027.01_manifest.json.digicert.chain.pem
```

Both must print `Verification: OK`. The time is in `openssl ts -reply -in <file>.tsr -text`.
Then check that the package you downloaded is the one stamped:

```bash
python tools/verify_issue.py almanac-2027.01 --digest bc834b2691f0f1c9fdee05a0c0fbae87958efe3a8d3e670aeff113f9b02b7949
```

The OpenTimestamps proof needs the `ots` client: `ots verify -f
docs/phase4/package_2027.01_manifest.json docs/phase4/proofs/package_2027.01_manifest.json.ots`.
The proof is complete: it commits the digest to the merkle root of Bitcoin block 977,029,
`141ca87affadf3b43e17e005215840a478fd20f1a237220226710f9eab01c4d1`. Without a Bitcoin node, run
`ots --no-bitcoin verify ...` and compare that root with any block explorer.

Why one maintainer and these proofs: [ADR 0005](../../adr/0005-single-maintainer.md).
