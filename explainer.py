def classify(item):
    n = item["name"].lower()

    if "defender" in n or "security" in n:
        return "critical"
    if "intel" in n or "amd" in n or "nvidia" in n:
        return "driver"
    if "update" in n:
        return "update"

    return "normal"

def explain(item):
    c = classify(item)

    if c == "critical":
        return "Critical system component. Not recommended to disable."
    if c == "driver":
        return "Driver-related component. May affect stability."
    if c == "update":
        return "Used for updates. Can usually be disabled."

    return "Third-party application. Usually safe to disable."
