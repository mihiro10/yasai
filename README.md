# 野菜価格統合ツール

取引先のCSVファイルを統合して、分析用のファイルを作成するWebアプリです。

## 使い方

1. ブラウザでアプリを開く
2. CSVファイルをアップロード
   - マルエイ市況.csv
   - 浜松ベジタブル単価表.csv
3. 「統合実行」ボタンをクリック
4. 結果をダウンロード

## ローカルで実行する場合

```bash
pip install -r requirements.txt
streamlit run consolidate_suppliers_web.py
```

## デプロイ

Streamlit Cloudでデプロイする場合、このリポジトリをそのまま使用できます。

