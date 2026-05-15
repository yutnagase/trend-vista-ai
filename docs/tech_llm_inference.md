# LLM推論 — llama-cpp-python + ELYZA-JP-8B

## LLMの役割

本プロジェクトでは、感情分析の数値データをもとに「世の中の空気感」を言葉でまとめる総評レポートの生成にLLMを使っている。OpenAIなどの外部APIは使わず、自分のマシン上でLLMを動かす構成。

重要なのは、LLMは「分析」をしないということ。スコア・乖離値・トピック感情はすべてコードで事前計算済みであり、LLMはそれらを自然言語に変換する翻訳機として機能する。

## 使っている技術

- **llama-cpp-python** — C++で書かれたLLM推論エンジン「llama.cpp」のPythonバインディング。GPUがなくてもCPUだけでLLMを動かせる
- **ELYZA-JP-8B** — ELYZA社が公開した日本語特化の8Bパラメータモデル。Meta社のLlama 3をベースに日本語能力を拡張する追加学習を行ったもの
- **GGUF形式** — モデルを量子化（圧縮）して保存するファイル形式。llama-cpp-pythonでCPU推論する場合はGGUF一択

## ローカルLLMを採用した理由

| 方式 | メリット | デメリット |
|------|---------|-----------|
| 外部API（OpenAI等） | 高品質、セットアップ不要 | 有料、データを外部送信する |
| ローカルLLM | 無料、データが外に出ない | メモリを食う、品質はやや劣る |

「分析対象のデータを外部に送らない」「ランニングコストゼロ」を優先してローカルLLMを採用している。

## 量子化

| 量子化レベル | サイズ目安（8Bモデル） | 品質 |
|-------------|----------------------|------|
| FP16（無圧縮） | ~16GB | 最高 |
| Q8 | ~8GB | ほぼ劣化なし |
| Q4_K_M | ~4.5GB | 実用的（本プロジェクトで採用） |
| Q2 | ~3GB | 日本語が崩れやすい |

Q4_K_Mは「4bit量子化、Mixed precision」の略で、重要な層は高精度を保ちつつ全体を圧縮する方式。12GBのRAMでBERTモデルと共存できるギリギリのラインである。

## 実装

### モデルの自動ダウンロード

初回起動時にHugging Faceからモデルファイル（約4.5GB）を自動ダウンロードする。

```python
from huggingface_hub import hf_hub_download

model_path = hf_hub_download(
    repo_id="elyza/Llama-3-ELYZA-JP-8B-GGUF",
    filename="Llama-3-ELYZA-JP-8B-q4_k_m.gguf",
    local_dir="models",
)
```

2回目以降はローカルに保存されたファイルを使うので、ダウンロードは発生しない。

### プロンプトの設計

感情分析の結果を構造化して渡し、分析の観点を明示する。

```python
prompt = f"""以下は「{keyword}」に関する複数ソースの感情分析データです。

■ メディア（30件）
  感情: スコア +0.10（ポジ20% / 中立70% / ネガ10%）
  頻出語: 首相, 訪問, 経済, 連携, 会談

■ はてなブックマーク（40件）
  感情: スコア -0.50（ポジ10% / 中立30% / ネガ60%）
  頻出語: 批判, 疑問, 対応, 問題, 指摘

■ 分析タイプ
  🔥 構造的乖離（最大乖離 0.60、ソース間で評価方向が逆転）

上記データに基づき、総合インサイトを日本語で作成してください。

■ 総合インサイト
① 概要（乖離の有無と程度）
② 数値根拠（スコアと乖離幅）
③ トピック分析（どの話題がポジ／ネガに寄与しているか）
④ 結論（このトピックの空気感）
"""
```

「要約して」のような曖昧な指示ではなく、具体的な観点を列挙することで出力の方向性を安定させている。

### 生成パラメータ

```python
output = llm(
    prompt,
    max_tokens=512,
    temperature=0.7,
    top_p=0.9,
    stop=["\n\n\n", "---", "以上"],
)
```

- `temperature=0.7` — 適度にバリエーションを持たせつつ、破綻しない程度の値
- `stop` — レポートが終わったら余計な文を生成しないように停止条件を設定

### メモリ管理

```python
@lru_cache
def get_report_generator() -> LLMReportGenerator:
    return LLMReportGenerator()
```

FastAPIのDependsと`@lru_cache`の組み合わせで、モデルはプロセス起動中に1回だけロードされる。リクエストのたびに再ロードされることはない。

### 非同期化

_referenceプロジェクトでは分析と同時にLLM推論を実行していたが、本プロジェクトでは`POST /api/report/{id}`として分離した。分析結果を先に返し、AI総評は必要に応じて後から生成する設計にしている。

## 動作に必要なスペック

- RAM: 12GB以上（BERT ~2GB + ELYZA 4.5GB + OS・その他）
- ディスク: 6GB以上（モデルファイル保存用）
- CPU: 4コア以上推奨（推論速度に影響）
- GPU: 不要（あれば `n_gpu_layers` を設定して高速化可能）

推論には1回あたり30秒〜2分程度かかる（CPUのみの場合）。

## 参考リンク

- [llama-cpp-python GitHub](https://github.com/abetlen/llama-cpp-python)
- [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- [ELYZA-JP-8B（Hugging Face）](https://huggingface.co/elyza/Llama-3-ELYZA-JP-8B-GGUF)
- [GGUF形式について](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md)
