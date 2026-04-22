import pandas as pd
import json
import re
import os

# load the raw Banks & Connell data
item_df = pd.read_csv("Referential version_Item level data.csv")
item_df.columns = [c.strip() for c in item_df.columns]

# clean up text fields
for i in range(len(item_df)):
    item_df.at[i, "category"] = re.sub(r"\s+", " ", str(item_df.at[i, "category"]).strip().lower())
    item_df.at[i, "domain"] = re.sub(r"\s+", " ", str(item_df.at[i, "domain"]).strip().lower())

# clean category member into answer column
item_df["answer"] = ""
for i in range(len(item_df)):
    raw = str(item_df.at[i, "category.member"]).strip().lower()
    item_df.at[i, "answer"] = re.sub(r"\s+", " ", raw)

# only keep concrete categories
item_df = item_df[item_df["domain"] == "concrete"].copy()
item_df = item_df.reset_index(drop=True)

# convert numeric columns
item_df["prod.freq"] = pd.to_numeric(item_df["prod.freq"], errors="coerce")

# filter out bad/noisy answers
keep = []
for i in range(len(item_df)):
    ans = item_df.at[i, "answer"]
    freq = item_df.at[i, "prod.freq"]

    # skip empty
    if pd.isna(ans) or ans == "":
        continue
    # skip long answers (more than 3 words)
    if len(ans.split()) > 3:
        continue
    # skip answers with weird characters
    if re.search(r"[,/;()]", ans):
        continue
    # skip rare answers (fewer than 2 people said it)
    if pd.isna(freq) or freq < 2:
        continue

    keep.append(i)

item_df = item_df.loc[keep].copy()
item_df = item_df.reset_index(drop=True)

# remove duplicate category-answer pairs, keep highest freq
item_df = item_df.sort_values(by=["category", "prod.freq"], ascending=[True, False])
item_df = item_df.drop_duplicates(subset=["category", "answer"], keep="first")
item_df = item_df.reset_index(drop=True)

# build answer lists per category sorted by frequency
cat_answers = {}
for i in range(len(item_df)):
    cat = item_df.at[i, "category"]
    ans = item_df.at[i, "answer"]
    if cat not in cat_answers:
        cat_answers[cat] = []
    if ans not in cat_answers[cat]:
        cat_answers[cat].append(ans)

# auto-generate pairs from banks & connell using loose filters
all_cats = sorted(cat_answers.keys())
bc_pairs = []
for idx1 in range(len(all_cats)):
    for idx2 in range(idx1 + 1, len(all_cats)):
        c1 = all_cats[idx1]
        c2 = all_cats[idx2]
        set1 = set(cat_answers[c1])
        set2 = set(cat_answers[c2])

        shared_count = len(set1 & set2)
        q1_unique = len(set1 - set2)
        q2_unique = len(set2 - set1)
        union_count = len(set1 | set2)

        if union_count == 0:
            continue

        jaccard = shared_count / union_count

        # need at least 2 bridge words, 3 unique on each side
        if shared_count < 2:
            continue
        if q1_unique < 3 or q2_unique < 3:
            continue
        # keep jaccard in reasonable range
        if jaccard < 0.05 or jaccard > 0.5:
            continue
        # avoid q2 being fully contained in q1
        if len(set2) > 0 and shared_count / len(set2) > 0.85:
            continue

        bc_pairs.append((c1, c2, cat_answers[c1], cat_answers[c2]))

print("Found " + str(len(bc_pairs)) + " Banks & Connell pairs")

# load LLM-generated pairs from all json files in this folder
llm_raw_pairs = []
for fname in os.listdir("."):
    if fname.startswith("geminiResponse") and fname.endswith(".json"):
        with open(fname, "r") as f:
            data = json.load(f)
        for entry in data:
            q1 = str(entry["q1_category"]).strip().lower()
            q2 = str(entry["q2_category"]).strip().lower()
            q1_list = [str(a).strip().lower() for a in entry["q1_answers"]]
            q2_list = [str(a).strip().lower() for a in entry["q2_answers"]]
            # drop duplicates while keeping order
            seen1 = set()
            clean1 = []
            for a in q1_list:
                if a not in seen1:
                    seen1.add(a)
                    clean1.append(a)
            seen2 = set()
            clean2 = []
            for a in q2_list:
                if a not in seen2:
                    seen2.add(a)
                    clean2.append(a)
            llm_raw_pairs.append((q1, q2, clean1, clean2))

print("Loaded " + str(len(llm_raw_pairs)) + " raw LLM pairs")

# validate LLM pairs with the same filters
llm_pairs = []
rejected = 0
for q1, q2, l1, l2 in llm_raw_pairs:
    set1 = set(l1)
    set2 = set(l2)

    shared_count = len(set1 & set2)
    q1_unique = len(set1 - set2)
    q2_unique = len(set2 - set1)
    union_count = len(set1 | set2)

    if union_count == 0:
        rejected += 1
        continue

    jaccard = shared_count / union_count

    if shared_count < 2:
        rejected += 1
        continue
    if q1_unique < 3 or q2_unique < 3:
        rejected += 1
        continue
    if jaccard < 0.05 or jaccard > 0.5:
        rejected += 1
        continue
    if len(set2) > 0 and shared_count / len(set2) > 0.85:
        rejected += 1
        continue

    llm_pairs.append((q1, q2, l1, l2))

print("Kept " + str(len(llm_pairs)) + " LLM pairs, rejected " + str(rejected))

# build the final dataset
rows = []

for q1, q2, l1, l2 in bc_pairs:
    q1_set = set(l1)
    q2_set = set(l2)

    shared = []
    for a in l1:
        if a in q2_set:
            shared.append(a)

    q1_only = []
    for a in l1:
        if a not in q2_set:
            q1_only.append(a)

    q2_only = []
    for a in l2:
        if a not in q1_set:
            q2_only.append(a)

    row = {
        "source": "banks_connell",
        "q1_category": q1,
        "q2_category": q2,
        "q1_answers_json": json.dumps(l1),
        "q2_answers_json": json.dumps(l2),
        "shared_answers_json": json.dumps(shared),
        "q1_only_answers_json": json.dumps(q1_only),
        "q2_only_answers_json": json.dumps(q2_only),
        "n_q1_answers": len(l1),
        "n_q2_answers": len(l2),
        "n_shared": len(shared),
        "n_q1_only": len(q1_only),
        "n_q2_only": len(q2_only),
    }
    rows.append(row)

for q1, q2, l1, l2 in llm_pairs:
    q1_set = set(l1)
    q2_set = set(l2)

    shared = []
    for a in l1:
        if a in q2_set:
            shared.append(a)

    q1_only = []
    for a in l1:
        if a not in q2_set:
            q1_only.append(a)

    q2_only = []
    for a in l2:
        if a not in q1_set:
            q2_only.append(a)

    row = {
        "source": "llm_generated",
        "q1_category": q1,
        "q2_category": q2,
        "q1_answers_json": json.dumps(l1),
        "q2_answers_json": json.dumps(l2),
        "shared_answers_json": json.dumps(shared),
        "q1_only_answers_json": json.dumps(q1_only),
        "q2_only_answers_json": json.dumps(q2_only),
        "n_q1_answers": len(l1),
        "n_q2_answers": len(l2),
        "n_shared": len(shared),
        "n_q1_only": len(q1_only),
        "n_q2_only": len(q2_only),
    }
    rows.append(row)

# save
out = pd.DataFrame(rows)
out.to_csv("impostor_pair_dataset.csv", index=False)
print("Saved impostor_pair_dataset.csv (" + str(len(rows)) + " total pairs)")