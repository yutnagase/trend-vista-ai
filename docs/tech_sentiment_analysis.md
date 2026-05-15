# 感情分析（Sentiment Analysis） — 複数BERTモデルのアンサンブル

## 概要

テキストが「ポジティブ」「ネガティブ」「中立」のどれに近いかを判定する自然言語処理の技術。本プロジェクトでは、Googleニュースの見出し・BlueSkyの投稿・はてブのコメントに対して感情分析を行い、各ソースの「空気感」を数値化している。

## 使っている技術

- **transformers** — Hugging Face社が開発した自然言語処理ライブラリ。学習済みモデルを簡単に呼び出せる
- **PyTorch** — モデル推論基盤。バッチ処理・softmax確率計算に使用

## アンサンブル構成

単一モデルでは中立寄りに保守的な出力をしやすい傾向があるため、異なるデータで学習された複数モデルの加重平均（ソフト投票）で判定している。

| モデル | 特性 | ウェイト |
|--------|------|----------|
| `koheiduck/bert-japanese-finetuned-sentiment` | 汎用・ニュース寄り。3クラス分類 | 0.334 |
| `christian-phu/bert-finetuned-japanese-sentiment` | レビュー特化。明確なポジ/ネガ検出力が高い | 0.333 |
| `llm-book/bert-base-japanese-v3-marc-ja` | MARC-jaデータセット。2クラスで「はっきり判定する」役割 | 0.333 |

### なぜアンサンブルか

- 単一モデル依存を避け、特定モデルの中立バイアスを相互補完
- 恣意性の排除（「人間がキーワードを決めた」ではなく「複数の学習済みモデルが合意した」）
- 各モデルが異なるデータで学習されているため、トレンド変化に強い

## 実装の構造

### アーキテクチャ概要

```
テキスト入力
    ↓
┌─────────────────────────────────────────────┐
│  Model 1 (koheiduck)     → [pos, neu, neg] × weight │
│  Model 2 (christian-phu) → [pos, neu, neg] × weight │
│  Model 3 (llm-book)     → [pos, neu, neg] × weight │
└─────────────────────────────────────────────┘
    ↓ 加重平均
最終スコア [pos, neu, neg]
    ↓
ラベル判定 (positive / neutral / negative)
```

### モデルのロードと推論

`transformers.pipeline` ではなく `AutoModelForSequenceClassification` + `AutoTokenizer` を直接使い、バッチ推論に対応している。

```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
model.eval()

# バッチ推論
encoded = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
with torch.no_grad():
    logits = model(**encoded).logits
    probs = torch.softmax(logits, dim=-1)
```

### ラベル体系の正規化

モデルごとに出力ラベルが異なる（`POSITIVE` / `LABEL_2` / `POS` など）。`model.config.id2label` を参照して自動的に positive / neutral / negative のインデックスにマッピングしている。

2クラスモデル（neutral出力なし）の場合は、`neutral = 1.0 - pos - neg` の残余として扱う。

### アンサンブル（加重平均）

```python
pos = sum(model_results[m]["positive"] * weights[m] for m in range(num_models))
neg = sum(model_results[m]["negative"] * weights[m] for m in range(num_models))
```

### 最終ラベルの決定

```python
if abs(pos - neg) < 0.1 or neu > max(pos, neg):
    final_label = "neutral"
elif pos > neg:
    final_label = "positive"
else:
    final_label = "negative"
```

- ポジティブとネガティブの差が0.1未満 → 中立
- 中立確率が最大 → 中立
- それ以外は大きい方のラベルを採用

### バッチ推論

1件ずつの推論ではなく、`BATCH_SIZE = 16` でまとめて処理する。3モデル×多数記事の推論でもパディング・並列計算の恩恵を受けられる。

### フォールバック設計

モデルのロードに失敗した場合、そのモデルをスキップしてウェイトを再正規化する。最低1モデルが動作すれば分析は継続される。

```python
total_weight = sum(u.weight for u in self._units)
for u in self._units:
    u.weight = u.weight / total_weight
```

## Net Sentiment Score

### 定義

ソーシャルリスニング・メディア分析業界で広く使われる指標。「ポジティブな声とネガティブな声の差引」で全体の論調を一つの数値に集約する。

```
Net Sentiment Score = positive比率 − negative比率
```

### 値域とラベル区間

| スコア範囲 | ラベル | 意味 |
|-----------|--------|------|
| +0.3 〜 +1.0 | ポジティブ優勢 | 肯定的な記事・投稿が明確に多い |
| +0.1 〜 +0.3 | ややポジ寄り | 肯定がやや優勢だが明確ではない |
| -0.1 〜 +0.1 | 中立的 | ポジティブとネガティブが拮抗 |
| -0.3 〜 -0.1 | やや懸念寄り | 否定がやや優勢だが明確ではない |
| -1.0 〜 -0.3 | ネガティブ優勢 | 否定的な記事・投稿が明確に多い |

### 閾値の根拠

- **±0.1** — BERTアンサンブルのラベル判定自体が `abs(pos - neg) < 0.1` で中立とするため、ラベル比率差も±0.1未満は統計的に意味のある偏りとは言えない
- **±0.3** — 30件中9件以上の差がある状態。母数が20〜30件の本プロジェクトでは、この水準を超えると明確な偏りと判断できる

## なぜローカル実行か

OpenAIのAPIなど外部サービスを使えばもっと高精度な感情分析もできるが、以下の理由でローカル実行を選んでいる。

- 分析対象のテキストを外部に送信しない（プライバシー保護）
- API利用料がかからない
- ネットワーク接続がなくても動作する

BERT-base × 3モデルで約1.2〜2.0GBのメモリを使用する。

## 参考リンク

- [Hugging Face transformers](https://huggingface.co/docs/transformers/)
- [koheiduck/bert-japanese-finetuned-sentiment](https://huggingface.co/koheiduck/bert-japanese-finetuned-sentiment)
- [christian-phu/bert-finetuned-japanese-sentiment](https://huggingface.co/christian-phu/bert-finetuned-japanese-sentiment)
- [llm-book/bert-base-japanese-v3-marc-ja](https://huggingface.co/llm-book/bert-base-japanese-v3-marc-ja)
