import os

# ❌ folders that MUST NOT be touched
BLACKLIST = (
    "User Data",
    "Default",
    "Profile",
    "Profiles",
    "Extensions",
    "Local Storage",
    "IndexedDB",
    "Service Worker",
    "VSCode",
    "Code\\User"
)

# ✅ allowed cache folders
WHITELIST = (
    "Cache",
    "Code Cache",
    "GPUCache",
    "Crashpad",
    "ShaderCache",
    "Logs",
    "Temp"
)


def is_safe_cache(path: str) -> bool:
    p = path.lower()

    for b in BLACKLIST:
        if b.lower() in p:
            return False

    for w in WHITELIST:
        if w.lower() in p:
            return True

    return False


def scan_directory(base_path):
    results = []

    for root, dirs, files in os.walk(base_path):
        if not is_safe_cache(root):
            continue

        for file in files:
            path = os.path.join(root, file)
            try:
                size = os.path.getsize(path)
                if size == 0:
                    continue

                results.append({
                    "path": path,
                    "size": round(size / (1024 * 1024), 2)
                })
            except:
                pass

    return results
