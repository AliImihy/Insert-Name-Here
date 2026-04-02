# Insert-Name-Here
CSCI 5541 Group Repository for Team Insert Name Here 
Team Members: Korra Ringgenberg, Sergio Moya, Ryan Vu, Ali Imihy


## Introduction and Motivation

Large Language Models (LLMs) are typically trained to be helpful, truthful,
and aligned with human preferences through instruction tuning and preference
optimization [1]. However, certain structured settings, such as social deduction
games, require strategic ambiguity and controlled deception.
In this project, we study whether modern alignment techniques can train an
LLM to act as a convincing impostor in a semantic deduction game. Unlike traditional alignment research, which focuses on increasing helpfulness and safety,
we explore whether these same methods can optimize for strategic blending and
misdirection in a controlled environment.



## Problem Definition and Methodology
We design a text-based game called Impostor. In each round:
1. Four players generate answers to a question.
2. Three players receive Question A.
3. One player (the impostor) receives a slightly different but semantically
related Question B.
4. All answers are revealed.
5. A judge or the non-impostor players must identify the impostor. 


Example:
* Q1: Name a tropical fruit.
* Q2: Name a citrus fruit.


If the impostor answers “orange,” it becomes difficult to identify the impostor since the answers can overlap in meaning.
The impostor succeeds if the judge fails to correctly identify them. Our main
research question is:
Does preference-based alignment (DPO) produce more convincing
impostor behavior than supervised fine-tuning (SFT)?
We compare three models: 
* A base pretrained LLM (zero-shot prompting)
* An SFT model trained on impostor-style responses
* A DPO-aligned model trained with preference pairs

The evaluation will be performed by simulating multiple game rounds and
measuring how often the impostor is not identified. A separate model (LLM-asa-judge) reviews all four answers and predicts the impostor to provide consistent
large-scale evaluation.
We can then analyze differences in language patterns across models to determine whether DPO produces more adaptive and context-aware deception
compared to SFT.

## Preliminary Findings

| q1               | q2                  | rounds | judge_accuracy | impostor_success | shared_rate | q2_only_rate | invalid_rate | valid_deception |
|------------------|---------------------|--------|----------------|------------------|-------------|--------------|--------------|------------------|
| animal           | farm animal         | 10     | 0.5            | 0.5              | 1           | 0            | 0            | 0.5              |
| bird             | water bird          | 10     | 0.2            | 0.8              | 0.7         | 0.1          | 0.2          | 0.6              |
| building         | human dwelling      | 10     | 0.2            | 0.8              | 0.9         | 0            | 0.1          | 0.8              |
| building         | religious building  | 10     | 0.2            | 0.8              | 1           | 0            | 0            | 0.8              |
| farm animal      | four-legged animal  | 10     | 0.6            | 0.4              | 0.6         | 0.4          | 0            | 0.4              |
| green vegetable  | vegetable           | 10     | 0.4            | 0.6              | 0.6         | 0.4          | 0            | 0.6              |
| herb             | spice               | 10     | 0.6            | 0.4              | 0.7         | 0.2          | 0.1          | 0.4              |
| insect           | stinging insect     | 10     | 0.3            | 0.7              | 0.7         | 0.2          | 0.1          | 0.6              |
| part of the body | part of the face    | 10     | 0.2            | 0.8              | 0.1         | 0.3          | 0.6          | 0.3              |
| averages         |                     |        | 0.3556         | 0.6444           | 0.7         | 0.1778       | 0.1222       | 0.5556           |
