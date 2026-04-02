import pandas as pd
import json
import re

# load the raw data
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
item_df["typicality"] = pd.to_numeric(item_df["typicality"], errors="coerce")

# filter out bad/noisy answers
keep = []
for i in range(len(item_df)):
    ans = item_df.at[i, "answer"]
    freq = item_df.at[i, "prod.freq"]
    typ = item_df.at[i, "typicality"]

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
    # skip low typicality
    if pd.isna(typ) or typ < 2.5:
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

# pairs we want in the final dataset
approved_pairs = [
    ("green vegetable", "vegetable"),
    ("bird", "water bird"),
    ("part of the body", "part of the face"),
    ("farm animal", "four-legged animal"),
    ("building", "religious building"),
    ("building", "human dwelling"),
    ("herb", "spice"),
    ("animal", "farm animal"),
    ("insect", "stinging insect"),
]

# build the final dataset
rows = []
for q1, q2 in approved_pairs:
    if q1 not in cat_answers or q2 not in cat_answers:
        continue

    q1_list = cat_answers[q1]
    q2_list = cat_answers[q2]
    q2_set = set(q2_list)
    q1_set = set(q1_list)

    # shared = answers in both, in q1 frequency order
    shared = []
    for a in q1_list:
        if a in q2_set:
            shared.append(a)

    # q1 only = in q1 but not q2, in q1 frequency order
    q1_only = []
    for a in q1_list:
        if a not in q2_set:
            q1_only.append(a)

    # q2 only = in q2 but not q1, in q2 frequency order
    q2_only = []
    for a in q2_list:
        if a not in q1_set:
            q2_only.append(a)

    row = {
        "q1_category": q1,
        "q2_category": q2,
        "q1_answers_json": json.dumps(q1_list),
        "q2_answers_json": json.dumps(q2_list),
        "shared_answers_json": json.dumps(shared),
        "q1_only_answers_json": json.dumps(q1_only),
        "q2_only_answers_json": json.dumps(q2_only),
        "n_q1_answers": len(q1_list),
        "n_q2_answers": len(q2_list),
        "n_shared": len(shared),
        "n_q1_only": len(q1_only),
        "n_q2_only": len(q2_only),
    }
    rows.append(row)

# save
out = pd.DataFrame(rows)
out.to_csv("impostor_pair_dataset.csv", index=False)
print("Saved impostor_pair_dataset.csv")