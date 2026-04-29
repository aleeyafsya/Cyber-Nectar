import json
import random
import copy

TARGET_PER_CLASS = 50

# Variations (safe, realistic)
USER_AGENTS = [
    "curl/7.68.0",
    "wget/1.21.1",
    "python-requests/2.31.0",
    "Go-http-client/1.1",
    "Mirai_Scanner",
    "Mirai_v2",
    "Nikto/2.1.6"
]

METHODS = ["GET", "POST", "HEAD"]

QUERY_VARIANTS = [
    "",
    "?cmd=ls",
    "?cmd=whoami",
    "?debug=true",
    "?test=1"
]

def load_seed(path="labeled_test_set.json"):
    with open(path, "r") as f:
        return json.load(f)

def mutate(entry):
    e = copy.deepcopy(entry)

    # Mutate user agent
    e["user_agent"] = random.choice(USER_AGENTS)

    # Mutate method (keep POST where required)
    if e["method"] == "GET":
        e["method"] = random.choice(METHODS)

    # Mutate path slightly
    if "?" not in e["path"]:
        e["path"] += random.choice(QUERY_VARIANTS)

    return e

def generate(seed):
    buckets = {"LOW": [], "MEDIUM": [], "HIGH": [], "CRITICAL": []}

    for e in seed:
        buckets[e["label"]].append(e)

    final = []

    for label, entries in buckets.items():
        if not entries:
            continue

        while len([e for e in final if e["label"] == label]) < TARGET_PER_CLASS:
            base = random.choice(entries)
            final.append(mutate(base))

    random.shuffle(final)
    return final

if __name__ == "__main__":
    seed = load_seed("labeled_test_set.json")  # your original JSON
    augmented = generate(seed)

    with open("dataset_200_balanced.json", "w") as f:
        json.dump(augmented, f, indent=2)

    print("dataset_200_balanced.json generated")
    print("Total samples:", len(augmented))
