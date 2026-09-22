# Human labeling rules

1. Inspect `cluster_profile.csv`; document why each cluster is suspicious, uncertain, or authentic-like.
2. Enter the agreed cluster-to-score mapping in `config/config.yaml`. Cluster IDs have no intrinsic meaning.
3. Review `Data_To_Label.csv` and assign `Target_Label` manually: 0 Kem, 1 Binh_thuong, 2 Uy_tin.
4. Save the reviewed file as `output/labeling/Data_Labeled.csv`. `Score_ThamKhao` is context only and must not generate ground truth.

Document annotators, rubric, disagreements, and resolution. Labels derived from the same model features create leakage and must be disclosed.
