# Setup App Store Release (iOS)

End-to-end guide for setting up Apple code signing, App Store Connect, and (optionally) GitHub Actions CI/CD for iOS TestFlight/App Store distribution.

All generated artifacts go under `.scratch/apple/` in the project root.

## Prerequisites

- An Apple Developer account (Organization or Individual) with the **Apple Developer Program** enrolled
- `openssl` available locally
- `gh` CLI authenticated (only if CI/CD step is chosen)
- The Xcode project must already exist with a valid bundle ID

## Phase 1: Gather project info

Ask the user for:

1. **Bundle ID** (e.g. `com.example.myapp`) -- check the Xcode project's `PRODUCT_BUNDLE_IDENTIFIER` in the `.pbxproj` if available
2. **Team name** (the org or individual name on the Apple Developer account)
3. **Developer name** (full name of the person generating the cert -- Apple ties the CSR to the individual even for org accounts)
4. **Developer email**
5. **Provisioning profile name** (suggest: `<App Name> AppStore`)

Confirm the bundle ID matches what's in the Xcode project. If it doesn't, warn the user and ask which to change.

## Phase 2: Apple Developer Portal (manual steps)

Walk the user through these steps. After each, ask them to confirm before proceeding.

### 2a. Register App ID (if not already done)

> 1. Go to [Identifiers](https://developer.apple.com/account/resources/identifiers/list)
> 2. Click **"+"** > **App IDs** > **App**
> 3. Description: `<app name>`
> 4. Bundle ID: **Explicit** > `<bundle-id>`
> 5. Enable any capabilities your app needs (Push Notifications, Sign in with Apple, etc.)
> 6. Continue > Register

Note: iOS and macOS can share one bundle ID but need separate provisioning profiles per platform.

### 2b. Create Apple Distribution Certificate

Tell the user:

> We'll generate the CSR and private key locally with openssl. This is more reliable than Keychain Access for CI portability.

Then run the openssl commands (see Phase 3).

After the CSR is generated, walk the user through:

> 1. Go to [Certificates](https://developer.apple.com/account/resources/certificates/list)
> 2. Click **"+"** > **Apple Distribution** > Continue
> 3. Upload the CSR file: `.scratch/apple/certificates/distribution.csr`
> 4. Download the `.cer` file
> 5. Save it as `.scratch/apple/certificates/distribution.cer`

### 2c. Create Provisioning Profile

> 1. Go to [Profiles](https://developer.apple.com/account/resources/profiles/list)
> 2. Click **"+"** > under **Distribution**, select **App Store Connect**
> 3. Select the App ID (bundle ID) created above
> 4. Select the Apple Distribution certificate just created
> 5. Name: `<provisioning-profile-name>`
> 6. Generate > Download
> 7. Save as `.scratch/apple/profiles/<profile-name>.mobileprovision`

## Phase 3: Generate signing artifacts

Run these commands to generate all artifacts. Create the directory first:

```bash
mkdir -p .scratch/apple/certificates .scratch/apple/profiles .scratch/apple/keys
```

### 3a. Generate CSR + private key

```bash
openssl req -new -newkey rsa:2048 -nodes \
  -keyout .scratch/apple/certificates/distribution.key \
  -out .scratch/apple/certificates/distribution.csr \
  -subj "/CN=<developer-name>/O=<team-name>/emailAddress=<developer-email>"
```

### 3b. Convert DER cert to PEM (after user downloads .cer from Apple)

```bash
openssl x509 \
  -in .scratch/apple/certificates/distribution.cer \
  -inform DER \
  -out .scratch/apple/certificates/distribution.pem \
  -outform PEM
```

### 3c. Create PKCS#12 bundle

Generate a random password for CI use:

```bash
P12_PASSWORD="<app-name>-ci-$(date +%Y)"

openssl pkcs12 -export \
  -out .scratch/apple/certificates/distribution.p12 \
  -inkey .scratch/apple/certificates/distribution.key \
  -in .scratch/apple/certificates/distribution.pem \
  -passout pass:"$P12_PASSWORD"
```

### 3d. Verify the p12

```bash
openssl pkcs12 -in .scratch/apple/certificates/distribution.p12 \
  -info -nokeys -passin pass:"$P12_PASSWORD" | grep subject
```

## Phase 4: App Store Connect (manual steps)

### 4a. Create API Key

> 1. Go to [App Store Connect > Users and Access > Integrations > Keys](https://appstoreconnect.apple.com/access/integrations/api)
> 2. Make sure you're on the **App Store Connect API** tab (not "In-App Purchase")
> 3. Click **"+"** > Name: `CI` > Role: **App Manager** > Generate
> 4. **Download the `.p8` file immediately** (only downloadable once!)
> 5. Save as `.scratch/apple/keys/AuthKey_<KEY_ID>.p8`
> 6. Note the **Key ID** (shown in the table, also in the filename)
> 7. Note the **Issuer ID** (shown at the top of the Keys page)

### 4b. Encryption Compliance

If the app does NOT use custom encryption (only Apple-provided: Keychain, URLSession/HTTPS, etc.), add to `Info.plist`:

```xml
<key>ITSAppUsesNonExemptEncryption</key>
<false/>
```

This prevents App Store Connect from asking about encryption compliance on every upload.

## Phase 5: Configure Xcode project for CI signing

The Xcode project needs Manual signing in its Release config for the app target only. This avoids applying provisioning profiles to SPM package targets (which don't support them).

In the `.pbxproj`, find the app target's **Release** `XCBuildConfiguration` and set:

```
CODE_SIGN_IDENTITY = "Apple Distribution";
CODE_SIGN_STYLE = Manual;
DEVELOPMENT_TEAM = <team-id>;
PROVISIONING_PROFILE_SPECIFIER = "<provisioning-profile-name>";
```

**Important**: do NOT set these on the xcodebuild command line. CLI build settings override ALL targets globally, including SPM packages, which causes "does not support provisioning profiles" errors.

The **Debug** config can stay as `Automatic` for local development.

To find the Team ID: it's in the downloaded certificate. Run:
```bash
openssl x509 -in .scratch/apple/certificates/distribution.pem -noout -subject
```
The `OU=` field is the Team ID.

## Phase 6: CI/CD Setup (optional)

Ask the user: **"Do you want to configure CI/CD on GitHub Actions?"**

If yes, ask for:
1. **GitHub repo** (e.g. `org/repo`)
2. **Secret prefix** (suggest: `<APP_NAME>_IOS_`, e.g. `PDK_IOS_`)

### 6a. Generate `.scratch/apple/Taskfile.yml`

Create a Taskfile that pushes all 6 secrets to GitHub:

```yaml
version: '3'
silent: true

tasks:
  secrets:push:
    desc: Push Apple signing secrets to GitHub for iOS CI
    vars:
      REPO: <github-repo>
      CERTS_DIR: '{{.ROOT_DIR}}/certificates'
      PROFILES_DIR: '{{.ROOT_DIR}}/profiles'
      KEYS_DIR: '{{.ROOT_DIR}}/keys'
      PREFIX: <SECRET_PREFIX>
      P12_PASSWORD: <p12-password>
      ASC_KEY_ID: <key-id>
      ASC_ISSUER_ID: <issuer-id>
    cmds:
      - |
        set -eu
        echo "pushing Apple signing secrets to {{.REPO}}"

        base64 -w0 "{{.CERTS_DIR}}/distribution.p12" \
          | gh secret set {{.PREFIX}}APPLE_CERTIFICATE_BASE64 --repo="{{.REPO}}"
        echo "  {{.PREFIX}}APPLE_CERTIFICATE_BASE64 ✓"

        gh secret set {{.PREFIX}}APPLE_CERTIFICATE_PASSWORD --repo="{{.REPO}}" --body="{{.P12_PASSWORD}}"
        echo "  {{.PREFIX}}APPLE_CERTIFICATE_PASSWORD ✓"

        base64 -w0 "{{.PROFILES_DIR}}/<profile-file>.mobileprovision" \
          | gh secret set {{.PREFIX}}PROVISIONING_PROFILE_BASE64 --repo="{{.REPO}}"
        echo "  {{.PREFIX}}PROVISIONING_PROFILE_BASE64 ✓"

        gh secret set {{.PREFIX}}ASC_KEY_ID --repo="{{.REPO}}" --body="{{.ASC_KEY_ID}}"
        echo "  {{.PREFIX}}ASC_KEY_ID ✓"

        gh secret set {{.PREFIX}}ASC_ISSUER_ID --repo="{{.REPO}}" --body="{{.ASC_ISSUER_ID}}"
        echo "  {{.PREFIX}}ASC_ISSUER_ID ✓"

        base64 -w0 "{{.KEYS_DIR}}/AuthKey_{{.ASC_KEY_ID}}.p8" \
          | gh secret set {{.PREFIX}}ASC_KEY_BASE64 --repo="{{.REPO}}"
        echo "  {{.PREFIX}}ASC_KEY_BASE64 ✓"

        echo "done — 6 secrets pushed"
```

### 6b. GitHub Secrets reference

| Secret | Contents |
|---|---|
| `<PREFIX>APPLE_CERTIFICATE_BASE64` | base64 of `distribution.p12` |
| `<PREFIX>APPLE_CERTIFICATE_PASSWORD` | p12 export password |
| `<PREFIX>PROVISIONING_PROFILE_BASE64` | base64 of `.mobileprovision` |
| `<PREFIX>ASC_KEY_ID` | App Store Connect API key ID |
| `<PREFIX>ASC_ISSUER_ID` | App Store Connect issuer ID |
| `<PREFIX>ASC_KEY_BASE64` | base64 of `AuthKey_<ID>.p8` |

### 6c. GitHub Actions workflow notes

Key patterns for the GHA workflow (not generated by this skill, but reference for whoever writes it):

**Certificate + profile install** (in a CI step):
```bash
# Decode from secrets
printf '%s' "$CERTIFICATE_BASE64" | base64 --decode -o "$RUNNER_TEMP/distribution.p12"
printf '%s' "$PROFILE_BASE64" | base64 --decode -o "$RUNNER_TEMP/profile.mobileprovision"

# Create temporary keychain
security create-keychain -p "" "$RUNNER_TEMP/build.keychain-db"
security set-keychain-settings -lut 21600 "$RUNNER_TEMP/build.keychain-db"
security unlock-keychain -p "" "$RUNNER_TEMP/build.keychain-db"
security import "$RUNNER_TEMP/distribution.p12" -P "$CERTIFICATE_PASSWORD" -A -t cert -f pkcs12 -k "$RUNNER_TEMP/build.keychain-db"
security set-key-partition-list -S apple-tool:,apple: -k "" "$RUNNER_TEMP/build.keychain-db"
security list-keychains -d user -s "$RUNNER_TEMP/build.keychain-db" login.keychain-db

# Install provisioning profile
mkdir -p ~/Library/MobileDevice/Provisioning\ Profiles
PROFILE_UUID=$(/usr/libexec/PlistBuddy -c "Print UUID" /dev/stdin <<< "$(security cms -D -i "$RUNNER_TEMP/profile.mobileprovision")")
cp "$RUNNER_TEMP/profile.mobileprovision" ~/Library/MobileDevice/Provisioning\ Profiles/"$PROFILE_UUID".mobileprovision
```

**TestFlight upload** (altool):
```bash
mkdir -p ~/private_keys
printf '%s' "$ASC_KEY_BASE64" | base64 --decode -o ~/private_keys/AuthKey_"$ASC_KEY_ID".p8

xcrun altool --upload-app \
  --type ios \
  --file "$RUNNER_TEMP/export/PdkIos.ipa" \
  --apiKey "$ASC_KEY_ID" \
  --apiIssuer "$ASC_ISSUER_ID"
```

**ExportOptions.plist** (for `xcodebuild -exportArchive`):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>method</key>
  <string>app-store-connect</string>
  <key>teamID</key>
  <string><team-id></string>
  <key>signingStyle</key>
  <string>manual</string>
  <key>provisioningProfiles</key>
  <dict>
    <key><bundle-id></key>
    <string><provisioning-profile-name></string>
  </dict>
  <key>uploadSymbols</key>
  <false/>
</dict>
</plist>
```

Do NOT include `<key>destination</key><string>upload</string>` -- it makes xcodebuild try to authenticate with ASC during export (without credentials). Use a separate altool step for upload.

## Gotchas

1. **Use `printf '%s'` not `echo`** when piping base64 secrets to `base64 --decode` -- `echo` appends a newline that corrupts binary files (p12, mobileprovision).
2. **`gh secret set NAME`** reads from stdin when piped. Do NOT use `--body=-` -- that sends the literal string `"-"`.
3. **Never set PROVISIONING_PROFILE_SPECIFIER on the xcodebuild CLI** -- it applies to ALL targets including SPM packages. Set it in the pbxproj for the app target's Release config only.
4. **`altool` doesn't accept `--PRIVATE_KEY <path>`** -- it only searches `~/private_keys/`, `~/.private_keys/`, `~/.appstoreconnect/private_keys/` for files named `AuthKey_<KEY_ID>.p8`.
5. **`CFBundleShortVersionString` (MARKETING_VERSION) must be 1-3 period-separated integers** -- no prerelease suffixes like `-exp`. Use a plain version (e.g. `0.0.0` for experimental) and differentiate builds via `CURRENT_PROJECT_VERSION` (build number, also must be numeric).
6. **Wrong cert type**: "Developer ID Application" is for Mac apps outside the App Store. For iOS/TestFlight, always use **Apple Distribution**.
7. **Keychain Access export is fragile**: if the cert is imported into a different keychain than where the CSR's private key lives, "Export as .p12" simply doesn't appear. Generating CSR+key with openssl avoids this entirely.
8. **`openssl pkcs12 -export`** does not accept `-inform DER` -- convert the `.cer` to PEM first with `openssl x509`.

## Output structure

```
.scratch/apple/
├── certificates/
│   ├── distribution.csr          # generated CSR
│   ├── distribution.key          # RSA 2048 private key
│   ├── distribution.cer          # downloaded from Apple (DER)
│   ├── distribution.pem          # PEM conversion
│   └── distribution.p12          # PKCS#12 bundle for CI
├── profiles/
│   └── <profile-name>.mobileprovision
├── keys/
│   └── AuthKey_<KEY_ID>.p8       # ASC API key
└── Taskfile.yml                  # secrets push task (if CI/CD chosen)
```
