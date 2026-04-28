#!/usr/bin/env python3
"""
Upload localized App Store metadata to App Store Connect.
Uses the App Store Connect API directly — no fastlane needed.

Usage: python3 fastlane/upload-metadata.py
"""

import subprocess, json, base64, time, urllib.request, urllib.error, os, sys

# --- Configuration ---
KEY_FILE = os.path.expanduser("~/.appstoreconnect/AuthKey_REDACTED.p8")
KEY_ID = "REDACTED_KEY"
ISSUER_ID = "REDACTED_ISSUER"
APP_ID = "REPLACE_WITH_APP_ID"
SUPPORT_URL = "https://corvusdevs.github.io/Red-Crow-For-Safari/"
MARKETING_URL = "https://corvusdevs.github.io/Red-Crow-For-Safari/"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
METADATA_DIR = os.path.join(SCRIPT_DIR, "metadata")

LOCALES = {
    "en-US": "en-US",
    "de-DE": "de-DE",
    "es-ES": "es-ES",
    "fr-FR": "fr-FR",
    "it": "it",
    "ja": "ja",
    "ko": "ko",
    "nl-NL": "nl-NL",
    "pt-BR": "pt-BR",
    "ru": "ru",
    "tr": "tr",
    "ar-SA": "ar-SA",
    "th": "th",
    "zh-Hans": "zh-Hans",
    "zh-Hant": "zh-Hant",
}

# --- JWT / API helpers ---

def b64url(data):
    if isinstance(data, str):
        data = data.encode()
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def der_to_raw(der_sig):
    idx = 2
    r_len = der_sig[idx + 1]
    r = der_sig[idx + 2 : idx + 2 + r_len]
    idx += 2 + r_len
    s_len = der_sig[idx + 1]
    s = der_sig[idx + 2 : idx + 2 + s_len]
    return r[-32:].rjust(32, b"\x00") + s[-32:].rjust(32, b"\x00")

def get_token():
    header = b64url(json.dumps({"alg": "ES256", "kid": KEY_ID, "typ": "JWT"}))
    now = int(time.time())
    payload = b64url(json.dumps({
        "iss": ISSUER_ID, "iat": now, "exp": now + 1200,
        "aud": "appstoreconnect-v1"
    }))
    proc = subprocess.run(
        ["openssl", "dgst", "-sha256", "-sign", KEY_FILE],
        input=f"{header}.{payload}".encode(), capture_output=True
    )
    sig = b64url(der_to_raw(proc.stdout))
    return f"{header}.{payload}.{sig}"

def api_request(method, url, body=None):
    headers = {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        if resp.status == 204:
            return None
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        try:
            return {"_error": True, "code": e.code, "body": json.loads(error_body)}
        except:
            print(f"  ERROR {e.code}: {error_body}")
            return None

def api_get(url):
    return api_request("GET", url)

def api_post(url, body):
    return api_request("POST", url, body)

def api_patch(url, body):
    return api_request("PATCH", url, body)

# --- Read metadata files ---

def read_metadata(folder_name):
    folder = os.path.join(METADATA_DIR, folder_name)
    result = {}
    for field, filename in [
        ("description", "description.txt"),
        ("keywords", "keywords.txt"),
        ("promotionalText", "promotional_text.txt"),
        ("whatsNew", "release_notes.txt"),
    ]:
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            with open(path, "r") as f:
                result[field] = f.read().strip()
    if SUPPORT_URL:
        result["supportUrl"] = SUPPORT_URL
    if MARKETING_URL:
        result["marketingUrl"] = MARKETING_URL
    return result

def read_subtitle(folder_name):
    path = os.path.join(METADATA_DIR, folder_name, "subtitle.txt")
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read().strip()
    return None

# --- Version localizations (description, keywords, etc.) ---

def get_editable_versions():
    url = (f"https://api.appstoreconnect.apple.com/v1/apps/{APP_ID}/appStoreVersions"
           f"?fields[appStoreVersions]=versionString,appStoreState,platform")
    data = api_get(url)
    versions = []
    for v in data["data"]:
        state = v["attributes"]["appStoreState"]
        if state in ("PREPARE_FOR_SUBMISSION", "WAITING_FOR_REVIEW", "IN_REVIEW"):
            versions.append(v)
    return versions

def get_existing_localizations(version_id):
    url = (f"https://api.appstoreconnect.apple.com/v1/appStoreVersions/{version_id}"
           f"/appStoreVersionLocalizations?fields[appStoreVersionLocalizations]=locale&limit=50")
    data = api_get(url)
    return {loc["attributes"]["locale"]: loc["id"] for loc in data["data"]}

def create_localization(version_id, locale, metadata):
    body = {
        "data": {
            "type": "appStoreVersionLocalizations",
            "attributes": {"locale": locale, **metadata},
            "relationships": {
                "appStoreVersion": {
                    "data": {"type": "appStoreVersions", "id": version_id}
                }
            }
        }
    }
    return api_post(
        "https://api.appstoreconnect.apple.com/v1/appStoreVersionLocalizations", body
    )

def update_localization(loc_id, metadata):
    body = {
        "data": {
            "type": "appStoreVersionLocalizations",
            "id": loc_id,
            "attributes": metadata,
        }
    }
    return api_patch(
        f"https://api.appstoreconnect.apple.com/v1/appStoreVersionLocalizations/{loc_id}",
        body,
    )

# --- App info localizations (subtitle) ---

def get_app_info():
    url = f"https://api.appstoreconnect.apple.com/v1/apps/{APP_ID}/appInfos?limit=5"
    data = api_get(url)
    for info in data["data"]:
        return info["id"]
    return None

def get_app_info_localizations(app_info_id):
    url = (f"https://api.appstoreconnect.apple.com/v1/appInfos/{app_info_id}"
           f"/appInfoLocalizations?fields[appInfoLocalizations]=locale&limit=50")
    data = api_get(url)
    return {loc["attributes"]["locale"]: loc["id"] for loc in data["data"]}

def create_app_info_localization(app_info_id, locale, subtitle):
    body = {
        "data": {
            "type": "appInfoLocalizations",
            "attributes": {"locale": locale, "subtitle": subtitle},
            "relationships": {
                "appInfo": {
                    "data": {"type": "appInfos", "id": app_info_id}
                }
            }
        }
    }
    return api_post(
        "https://api.appstoreconnect.apple.com/v1/appInfoLocalizations", body
    )

def update_app_info_localization(loc_id, subtitle):
    body = {
        "data": {
            "type": "appInfoLocalizations",
            "id": loc_id,
            "attributes": {"subtitle": subtitle},
        }
    }
    return api_patch(
        f"https://api.appstoreconnect.apple.com/v1/appInfoLocalizations/{loc_id}",
        body,
    )

# --- Main logic ---

def upload_for_version(version):
    version_id = version["id"]
    platform = version["attributes"]["platform"]
    version_str = version["attributes"]["versionString"]
    state = version["attributes"]["appStoreState"]

    print(f"\n{'='*60}")
    print(f"  {platform} v{version_str} ({state})")
    print(f"{'='*60}")

    can_edit_whats_new = state == "PREPARE_FOR_SUBMISSION"

    existing = get_existing_localizations(version_id)
    print(f"  Existing localizations: {', '.join(sorted(existing.keys()))}")
    if not can_edit_whats_new:
        print(f"  Note: skipping whatsNew (not editable in {state})")

    for folder_name, asc_locale in LOCALES.items():
        metadata = read_metadata(folder_name)
        if not metadata:
            print(f"  [{asc_locale}] No metadata files found — skipping")
            continue

        if not can_edit_whats_new:
            metadata.pop("whatsNew", None)

        if asc_locale in existing:
            result = update_localization(existing[asc_locale], metadata)
        else:
            result = create_localization(version_id, asc_locale, metadata)

        if result and result.get("_error"):
            errors = result.get("body", {}).get("errors", [])
            whats_new_error = any("whatsNew" in (e.get("detail", "") + e.get("title", "")) for e in errors)
            promo_error = any("Promotional" in e.get("detail", "") for e in errors)
            if whats_new_error:
                metadata.pop("whatsNew", None)
                print(f"  [{asc_locale}] Retrying without whatsNew...")
                if asc_locale in existing:
                    result = update_localization(existing[asc_locale], metadata)
                else:
                    result = create_localization(version_id, asc_locale, metadata)
            elif promo_error:
                print(f"  [{asc_locale}] FAILED — promotional text too long")
                continue
            else:
                for e in errors:
                    print(f"  [{asc_locale}] ERROR: {e.get('detail', e.get('title', 'Unknown'))}")
                continue

        action = "updated" if asc_locale in existing else "created"
        if result and not result.get("_error"):
            print(f"  [{asc_locale}] {action} — {', '.join(metadata.keys())}")
        else:
            print(f"  [{asc_locale}] FAILED")

def upload_subtitles():
    print(f"\n{'='*60}")
    print(f"  Uploading subtitles (app info localizations)")
    print(f"{'='*60}")

    app_info_id = get_app_info()
    if not app_info_id:
        print("  Could not find app info — skipping subtitles")
        return

    existing = get_app_info_localizations(app_info_id)
    print(f"  Existing app info locales: {', '.join(sorted(existing.keys()))}")

    for folder_name, asc_locale in LOCALES.items():
        subtitle = read_subtitle(folder_name)
        if not subtitle:
            continue

        if asc_locale in existing:
            result = update_app_info_localization(existing[asc_locale], subtitle)
        else:
            result = create_app_info_localization(app_info_id, asc_locale, subtitle)

        if result and result.get("_error"):
            errors = result.get("body", {}).get("errors", [])
            for e in errors:
                print(f"  [{asc_locale}] ERROR: {e.get('detail', e.get('title', 'Unknown'))}")
            continue

        action = "updated" if asc_locale in existing else "created"
        if result and not result.get("_error"):
            print(f"  [{asc_locale}] subtitle {action}: {subtitle}")
        else:
            print(f"  [{asc_locale}] subtitle FAILED")

def main():
    if APP_ID == "REPLACE_WITH_APP_ID":
        print("Set APP_ID in the script before running.")
        sys.exit(1)

    if not os.path.exists(KEY_FILE):
        print(f"API key not found: {KEY_FILE}")
        sys.exit(1)

    print("Fetching editable app store versions...")
    versions = get_editable_versions()

    if not versions:
        print("No editable versions found (need PREPARE_FOR_SUBMISSION or WAITING_FOR_REVIEW).")
        sys.exit(1)

    for v in versions:
        p = v["attributes"]["platform"]
        s = v["attributes"]["appStoreState"]
        print(f"  Found: {p} v{v['attributes']['versionString']} ({s})")

    for version in versions:
        upload_for_version(version)

    upload_subtitles()

    print(f"\nDone!")

if __name__ == "__main__":
    main()
