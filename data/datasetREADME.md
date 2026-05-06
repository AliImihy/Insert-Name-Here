# Dataset Build Script

Builds the impostor game dataset. Each row is a pair of related categories (q1, q2) with their answer lists and precomputed set operations.

Output: `impostor_pair_dataset.csv`

## Columns in the output

- `source` - `banks_connell` or `llm_generated`
- `q1_category`, `q2_category` - the two categories
- `q1_answers_json`, `q2_answers_json` - full answer lists as json
- `shared_answers_json` - answers that fit both categories
- `q1_only_answers_json`, `q2_only_answers_json` - answers that only fit one side
- `n_q1_answers`, `n_q2_answers`, `n_shared`, `n_q1_only`, `n_q2_only` - counts

## Input files

These need to be in the same folder as the script:

- `Referential version_Item level data.csv` - raw Banks & Connell category production norms (3067 rows, 67 concrete categories)
- `geminiResponse*.json` - gemini-generated pairs. The script loads every file starting with `geminiResponse` and ending in `.json`. Each entry has `q1_category`, `q2_category`, `q1_answers`, `q2_answers`.

## What the script does

1. Load Banks & Connell, lowercase and clean the text fields.
2. Keep only concrete categories (drop abstract ones).
3. Filter out bad answers: empty, more than 3 words, weird punctuation, or said by fewer than 2 people.
4. Drop duplicate (category, answer) pairs, keeping the highest frequency one.
5. Try every pair of categories and keep the pair if:
    - at least 2 shared answers
    - at least 3 unique answers on each side
    - jaccard between 0.05 and 0.5
    - q2 is not almost fully contained in q1 (shared / len(q2) <= 0.85)
6. Load all `geminiResponse*.json` files, lowercase them, dedupe answer lists.
7. Run the same filter on the llm pairs.
8. For each surviving pair, compute shared / q1_only / q2_only and build a row.
9. Save to `impostor_pair_dataset.csv`.

## Running it

```
python build_dataset.py
```

Expected output:

```
Found 36 Banks & Connell pairs
Loaded 80 raw LLM pairs
Kept 80 LLM pairs, rejected 0
Saved impostor_pair_dataset.csv (116 total pairs)
```

## Adding more data

Drop more `geminiResponse*.json` files in the folder and run the script again.

## Changing the filter thresholds

The filter values are hardcoded in two places (one for Banks & Connell, one for LLM pairs). If you change one make sure to change the other so both sources stay consistent.

## Why Banks & Connell

Their data is single-round category production which is the same mechanic as our game. Real human responses with frequency data so we know which items are typical for a category. Mafia / Werewolf datasets were considered but those are multi-turn dialogue, wrong format for our setup.

## Why LLM-generated pairs

Banks & Connell only has 67 concrete categories and even loose filters only yield ~36 pairs. We needed more pairs to scale up the dataset, so the rest are Gemini-generated and validated with the same filter so the distributions stay comparable.