# Human labeling rules

1. Inspect `cluster_profile.csv`; document why each cluster is suspicious, uncertain, or authentic-like.
2. Enter the agreed cluster-to-score mapping in `config/config.yaml`. Cluster IDs have no intrinsic meaning.
3. Review `Data_To_Label.csv` and assign `Target_Label` manually: 0 Kem, 1 Binh_thuong, 2 Uy_tin.
4. Save the reviewed file as `output/labeling/Data_Labeled.csv`. `Score_ThamKhao` is context only and must not generate ground truth.

Document annotators, rubric, disagreements, and resolution. Labels derived from the same model features create leakage and must be disclosed.

## Three-class rubric

- `0 = Kem`: multiple verified risk indicators or consistently poor service/quality evidence.
- `1 = Binh_thuong`: mixed evidence, material uncertainty, or neither strong risk nor strong reputation evidence.
- `2 = Uy_tin`: consistently strong evidence across service, product transparency, customer feedback, and authorized commercial metrics.

Each label requires `Labeler`, `Label_Reason`, and `Review_Status=approved`. At least two members review disputed cases; record both initial labels and the agreed resolution in meeting notes. Each class needs at least five shops before training.

## Current cluster decision

The mapping must be reviewed again whenever clustering is rerun because cluster IDs can change. For the current fingerprint, the reviewed profile is interpreted as follows:

- Cluster `0 -> 1.0`: overwhelmingly positive reviews with images; authentic-like pattern.
- Cluster `1 -> 0.0`: uniformly five-star, positive, shorter reviews without images; suspicious-pattern group, not proof of fraud.
- Cluster `2 -> 0.5`: very small mixed-rating group; insufficient evidence, therefore uncertain.
