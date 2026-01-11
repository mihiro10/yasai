# 野菜価格統合ツール

取引先のCSVファイルを統合して、分析用のファイルを作成するWebアプリです。

## 📁 ファイル構成

### メインファイル（必須）
- `consolidate_suppliers_web.py` - Streamlit Webアプリ（メイン）
- `requirements.txt` - 必要なPythonライブラリ

### フォルダ構成
- `samples/` - サンプルCSVファイル（テスト用）
- `reference/` - 参考ファイル
- `output/` - 生成された統合ファイル（再生成可能）
- `archive/` - 古いバージョンや不要なファイル
- `past_data/` - 過去データとグラフ

## 🚀 使い方

### ローカルで実行

```bash
pip install -r requirements.txt
streamlit run consolidate_suppliers_web.py
```

ブラウザで `http://localhost:8501` が開きます。

### Webで共有（Streamlit Cloud）

1. GitHubリポジトリ: https://github.com/mihiro10/yasai
2. Streamlit Cloud: https://share.streamlit.io/
3. リポジトリを接続してデプロイ

## 📝 ファイル名の形式

**必須形式:** `取引先名_YYYY_MM_DD.csv`

- 例: `マルエイ_2025_12_22.csv`
- 例: `浜松ベジタブル_2026_01_12.csv`

**重要:**
- アンダースコア（_）で区切る
- 日付は `YYYY_MM_DD` 形式（アンダースコア区切り）
- 日付は**月曜日**である必要があります

## ✅ 対応取引先

- マルエイ
- 浜松ベジタブル
- おやさい（準備中）
- アグリ（準備中）

## 📊 出力形式

- タブ区切りテキスト（Google Sheetsにコピペ可能）
- CSV形式
- Excel形式

## 🔧 トラブルシューティング

- ファイル名の形式を確認
- 日付が月曜日か確認
- 取引先名が正しいか確認
