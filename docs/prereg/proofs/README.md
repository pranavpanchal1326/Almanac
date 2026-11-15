# Timestamp proofs for issue 2027.01

What is timestamped is one file, `docs/prereg/2027.01.bundle.sha256`. It lists the SHA-256 of the
pre-registration, the code commit id, every source, tool, test and configuration file, the
evidence it relies on, and (through the data manifest) all 8,128 data files. Only the bundle's
own SHA-256 was sent to the timestamp services; no content left the machine.

| Proof | Service | Standard |
|---|---|---|
| `2027.01.bundle.sha256.freetsa.tsr` | FreeTSA (freetsa.org) | RFC 3161 |
| `2027.01.bundle.sha256.digicert.tsr` | DigiCert (timestamp.digicert.com) | RFC 3161 |
| `2027.01.bundle.sha256.ots` | OpenTimestamps public calendars, anchored in Bitcoin | OpenTimestamps |

Each `.tsq` is the query sent; each `.chain.pem` holds the certificates carried in the token;
`freetsa.ca.pem` is FreeTSA's published root; `*.verify.txt` is the verification output at
stamping time.

## Verify, from a clean checkout

1. The bundle covers the files you have:

   ```bash
   sha256sum -c docs/prereg/2027.01.bundle.sha256
   ```

2. The code commit named in the bundle is the one you checked out:

   ```bash
   git rev-parse HEAD^{commit} && cat docs/prereg/2027.01.code-commit.txt
   ```

   The proofs are committed after the stamped commit, so `HEAD` will be later; check that the named
   commit is an ancestor: `git merge-base --is-ancestor $(cat docs/prereg/2027.01.code-commit.txt) HEAD`.

3. The RFC 3161 tokens (OpenSSL 3):

   ```bash
   cd docs/prereg/proofs
   openssl ts -verify -data ../2027.01.bundle.sha256 -in 2027.01.bundle.sha256.freetsa.tsr -CAfile 2027.01.bundle.sha256.freetsa.ca.pem -untrusted 2027.01.bundle.sha256.freetsa.chain.pem
   ```

   ```bash
   openssl ts -verify -data ../2027.01.bundle.sha256 -in 2027.01.bundle.sha256.digicert.tsr -CAfile /etc/ssl/certs/ca-certificates.crt -untrusted 2027.01.bundle.sha256.digicert.chain.pem
   ```

   Both must print `Verification: OK`. The time is in `openssl ts -reply -in <file>.tsr -text`.

4. The OpenTimestamps proof (needs the `ots` client; full verification needs a Bitcoin node or
   trusts a block explorer):

   ```bash
   ots verify -f docs/prereg/2027.01.bundle.sha256 docs/prereg/proofs/2027.01.bundle.sha256.ots
   ```

   Right after stamping the proof is pending: the calendars have the digest but no Bitcoin block
   has confirmed it. `ots upgrade` fetches the completed proof a few hours later; the upgraded
   file replaces the pending one in a later commit, which changes no other file.

A changed bundle fails step 3 with "message imprint mismatch" (checked at stamping time).
