#!/usr/bin/env python3
"""
Upload Mac App Store screenshots to App Store Connect.
Uses the App Store Connect API directly.

Usage: python3 fastlane/upload-screenshots.py
"""

import subprocess, json, base64, time, urllib.request, urllib.error, os, sys, hashlib

# --- Configuration ---
KEY_FILE = os.path.expanduser("~/.appstoreconnect/AuthKey_REDACTED.p8")
KEY_ID = "REDACTED_KEY"
ISSUER_ID = "REDACTED_ISSUER"
APP_ID = "6765793100"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOTS_DIR = os.path.join(SCRIPT_DIR, "screenshots")

DISPLAY_TYPE = "APP_DESKTOP_2880_1800"

LOCALES = [
    "en-US", "de-DE", "es-ES", "fr-FR", "it", "ja", "ko",
    "nl-NL", "pt-BR", "ru", "tr", "ar-SA", "th", "zh-Hans", "zh-Hant",
]

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

def api_request(method, url, body=None, content_type="application/json"):
    headers = {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": content_type,
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
            parsed = json.loads(error_body)
            return {"_error": True, "code": e.code, "body": parsed}
        except:
            print(f"  ERROR {e.code}: {error_body[:500]}")
            return {"_error": True, "code": e.code}

def api_get(url):
    return api_request("GET", url)

def api_post(url, body):
    return api_request("POST", url, body)

def api_patch(url, body):
    return api_request("PATCH", url, body)

def api_delete(url):
    return api_request("DELETE", url)

def upload_binary(url, data, content_type="application/octet-stream"):
    headers = {
        "Content-Type": content_type,
        "Content-Length": str(len(data)),
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="PUT")
    try:
        resp = urllib.request.urlopen(req)
        return True
    except urllib.error.HTTPError as e:
        print(f"  Upload ERROR {e.code}: {e.read().decode()[:300]}")
        return False

# --- Screenshot upload flow ---

def get_editable_version():
    url = (f"https://api.appstoreconnect.apple.com/v1/apps/{APP_ID}/appStoreVersions"
           f"?fields[appStoreVersions]=versionString,appStoreState,platform")
    data = api_get(url)
    for v in data["data"]:
        state = v["attributes"]["appStoreState"]
        if state in ("PREPARE_FOR_SUBMISSION", "WAITING_FOR_REVIEW", "IN_REVIEW"):
            return v
    return None

def get_localizations(version_id):
    url = (f"https://api.appstoreconnect.apple.com/v1/appStoreVersions/{version_id}"
           f"/appStoreVersionLocalizations?fields[appStoreVersionLocalizations]=locale&limit=50")
    data = api_get(url)
    return {loc["attributes"]["locale"]: loc["id"] for loc in data["data"]}

def get_screenshot_sets(loc_id):
    url = (f"https://api.appstoreconnect.apple.com/v1/appStoreVersionLocalizations/{loc_id}"
           f"/appScreenshotSets?fields[appScreenshotSets]=screenshotDisplayType&limit=50")
    data = api_get(url)
    return {s["attributes"]["screenshotDisplayType"]: s["id"] for s in data["data"]}

def create_screenshot_set(loc_id, display_type):
    body = {
        "data": {
            "type": "appScreenshotSets",
            "attributes": {"screenshotDisplayType": display_type},
            "relationships": {
                "appStoreVersionLocalization": {
                    "data": {"type": "appStoreVersionLocalizations", "id": loc_id}
                }
            }
        }
    }
    result = api_post("https://api.appstoreconnect.apple.com/v1/appScreenshotSets", body)
    if result and not result.get("_error"):
        return result["data"]["id"]
    print(f"  Failed to create screenshot set: {result}")
    return None

def get_existing_screenshots(set_id):
    url = (f"https://api.appstoreconnect.apple.com/v1/appScreenshotSets/{set_id}"
           f"/appScreenshots?fields[appScreenshots]=fileName,fileSize&limit=50")
    data = api_get(url)
    if data and not data.get("_error"):
        return data["data"]
    return []

def delete_screenshot(screenshot_id):
    api_delete(f"https://api.appstoreconnect.apple.com/v1/appScreenshots/{screenshot_id}")

def reserve_screenshot(set_id, filename, file_size):
    body = {
        "data": {
            "type": "appScreenshots",
            "attributes": {
                "fileName": filename,
                "fileSize": file_size,
            },
            "relationships": {
                "appScreenshotSet": {
                    "data": {"type": "appScreenshotSets", "id": set_id}
                }
            }
        }
    }
    return api_post("https://api.appstoreconnect.apple.com/v1/appScreenshots", body)

def commit_screenshot(screenshot_id, checksum):
    body = {
        "data": {
            "type": "appScreenshots",
            "id": screenshot_id,
            "attributes": {
                "uploaded": True,
                "sourceFileChecksum": checksum,
            }
        }
    }
    return api_patch(
        f"https://api.appstoreconnect.apple.com/v1/appScreenshots/{screenshot_id}",
        body,
    )

def upload_screenshot_file(set_id, filepath):
    filename = os.path.basename(filepath)
    file_data = open(filepath, "rb").read()
    file_size = len(file_data)
    checksum = hashlib.md5(file_data).hexdigest()

    reservation = reserve_screenshot(set_id, filename, file_size)
    if not reservation or reservation.get("_error"):
        errors = reservation.get("body", {}).get("errors", []) if reservation else []
        for e in errors:
            print(f"    Reserve error: {e.get('detail', e.get('title', 'Unknown'))}")
        return False

    screenshot_id = reservation["data"]["id"]
    operations = reservation["data"]["attributes"].get("uploadOperations", [])

    for op in operations:
        url = op["url"]
        offset = op["offset"]
        length = op["length"]
        chunk = file_data[offset:offset + length]

        req_headers = {h["name"]: h["value"] for h in op["requestHeaders"]}
        req = urllib.request.Request(url, data=chunk, headers=req_headers, method=op["method"])
        try:
            urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            print(f"    Upload chunk error: {e.code}")
            return False

    result = commit_screenshot(screenshot_id, checksum)
    if result and not result.get("_error"):
        return True
    if result and result.get("_error"):
        errors = result.get("body", {}).get("errors", [])
        for e in errors:
            print(f"    Commit error: {e.get('detail', e.get('title', 'Unknown'))}")
    return False

# --- Main ---

def main():
    screenshot_files = sorted([
        os.path.join(SCREENSHOTS_DIR, f)
        for f in os.listdir(SCREENSHOTS_DIR)
        if f.endswith(".png")
    ])

    if not screenshot_files:
        print("No PNG files found in screenshots directory.")
        sys.exit(1)

    print(f"Found {len(screenshot_files)} screenshots:")
    for f in screenshot_files:
        print(f"  {os.path.basename(f)}")

    print("\nFetching editable version...")
    version = get_editable_version()
    if not version:
        print("No editable version found.")
        sys.exit(1)

    version_id = version["id"]
    platform = version["attributes"]["platform"]
    version_str = version["attributes"]["versionString"]
    state = version["attributes"]["appStoreState"]
    print(f"  {platform} v{version_str} ({state})")

    print("\nFetching localizations...")
    localizations = get_localizations(version_id)
    print(f"  Found: {', '.join(sorted(localizations.keys()))}")

    for locale in LOCALES:
        if locale not in localizations:
            print(f"\n[{locale}] No localization found — skipping")
            continue

        loc_id = localizations[locale]
        print(f"\n[{locale}] Processing...")

        sets = get_screenshot_sets(loc_id)
        set_id = sets.get(DISPLAY_TYPE)

        if not set_id:
            set_id = create_screenshot_set(loc_id, DISPLAY_TYPE)
            if not set_id:
                print(f"  Could not create screenshot set — skipping")
                continue
            print(f"  Created screenshot set ({DISPLAY_TYPE})")
        else:
            existing = get_existing_screenshots(set_id)
            if existing:
                print(f"  Deleting {len(existing)} existing screenshots...")
                for ss in existing:
                    delete_screenshot(ss["id"])
                time.sleep(1)

        for filepath in screenshot_files:
            fname = os.path.basename(filepath)
            ok = upload_screenshot_file(set_id, filepath)
            status = "uploaded" if ok else "FAILED"
            print(f"  {fname}: {status}")

    print(f"\nDone!")

if __name__ == "__main__":
    main()
