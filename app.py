#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
野菜価格統合ツール（統一品名マッピング付き）
Streamlit Webアプリ
"""
import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
from io import StringIO

st.set_page_config(page_title="野菜価格統合ツール", layout="wide")

st.title("🥬 野菜価格統合ツール（統一品名マッピング付き）")
st.markdown("CSVファイルをアップロードして、データを自動で整理し、統一品名（カタカナ）をマッピングします。")

# 使い方の説明を展開可能なセクションに追加
with st.expander("📖 使い方ガイド", expanded=False):
    st.markdown("""
    ### ステップ1: ファイル名を準備
    
    CSVファイルの名前を以下の形式に変更してください：
    
    **形式:** `取引先名_YYYY_MM_DD.csv`
    
    **例:**
    - `マルエイ_2025_12_22.csv`
    - `浜松ベジタブル_2026_01_12.csv`
    - `アグリ_2026_01_19.csv`
    
    **重要:**
    - アンダースコア（_）で区切る必要があります
    - 日付は `YYYY_MM_DD` 形式（アンダースコア区切り）
    - 日付は**月曜日**である必要があります
    
    ### ステップ2: ファイルをアップロード
    
    1. 「CSVファイルをアップロード（1ファイルのみ）」セクションでファイルを選択
    2. ドラッグ&ドロップまたは「Browse files」ボタンでファイルを選択
    3. ファイル名が正しい形式か確認（取引先名と日付が表示されます）
    
    ### ステップ3: データを整理
    
    1. 「🔄 データを整理」ボタンをクリック
    2. データが処理されます（数秒かかります）
    
    ### ステップ4: 結果を確認
    
    1. **警告の確認**
       - マッピングされていない品名がある場合、黄色の警告が表示されます
       - 未マッピングの品名が一覧表示されます
    
    2. **データの確認**
       - データ数、取引先、週が表示されます
       - データプレビューで全データを確認できます
    
    3. **データのコピー**
       - 「📋 コピー&ペースト用データ」セクションのデータをコピー
       - Google SheetsやExcelに貼り付け可能（タブ区切り形式）
    
    ### 出力データの形式
    
    出力されるデータには以下の列が含まれます：
    
    1. **品名** - 元の品名
    2. **統一品名（カタカナ）** - マッピングされた統一品名
    3. **取引先** - マルエイ、浜松ベジタブル、アグリ、おやさい
    4. **産地** - 産地情報
    5. **kg単価** - キログラム単価
    6. **その週** - 週の日付（月曜日）
    
    ### ⚠️ よくあるエラー
    
    **「サポートされていない取引先です」**
    - ファイル名に取引先名が正しく含まれているか確認
    - 対応取引先: マルエイ、浜松ベジタブル、アグリ、おやさい
    
    **「ファイル名の日付は月曜日である必要があります」**
    - ファイル名の日付が月曜日か確認
    
    **「データが抽出されませんでした」**
    - CSVファイルの形式を確認
    - ファイルが正しい取引先の形式か確認
    """)

# Supported vendors
SUPPORTED_VENDORS = ['マルエイ', '浜松ベジタブル', 'おやさい', 'アグリ']

# 統一品名マッピング辞書
UNIFIED_NAME_MAPPING = {
    'ごぼう': 'ゴボウ',
    'さつま芋': 'サツマイモ',
    'さつま芋2L': 'サツマイモ',
    '人参': 'ニンジン',
    '人参A2L': 'ニンジン',
    '人参B2L': 'ニンジン',
    '人参L': 'ニンジン',
    '人参L・2L': 'ニンジン',
    '大根': 'ダイコン',
    '玉ねぎ': 'タマネギ',
    '玉ねぎM・L・L大': 'タマネギ',
    'メークイン': 'ジャガイモ',
    'キャベツ': 'キャベツ',
    '加工キャベツ': 'キャベツ',
    '小松菜': 'コマツナ',
    '小松菜加工用': 'コマツナ',
    '玉レタス': 'レタス',
    '白菜': 'ハクサイ',
    '白ネギ': 'ネギ',
    'パプリカ': 'パプリカ',
    'パプリカA品': 'パプリカ',
    'ピーマン': 'ピーマン',
    'ししとう': 'シシトウ',
    'ミニトマト': 'ミニトマト',
    'トマト': 'トマト',
    '丸トマト': 'トマト',
    '丸トマトM玉': 'トマト',
    'ブロッコリー': 'ブロッコリー',
    '胡瓜': 'キュウリ',
    '茄子L': 'ナス',
    '茄子優2L': 'ナス',
    '南瓜': 'カボチャ',
    '国産鶏もも肉チルド': 'チキン',
    '国産鶏ムネ肉チルド': 'チキン',
    '鶏卵LL': 'タマゴ',
    '鶏卵LLかL': 'タマゴ',
    '鶏卵MS': 'タマゴ',
    '同上': None,
    'ほうれん草': 'ホウレンソウ',
    '水菜': 'ミズナ',
    'チンゲン菜': 'チンゲンサイ',
    '青梗菜': 'チンゲンサイ',
    'グリーンリーフ': 'レタス',
    'サニーレタス': 'レタス',
    'サラダ菜': 'レタス',
    '三つ葉': 'ミツバ',
    '大葉': 'シソ',
    'パセリ': 'パセリ',
    'パクチー': 'パクチー',
    '豆苗': 'トウミョウ',
    'もやし': 'モヤシ',
    'ピュフレもやし': 'モヤシ',
    '大豆もやし': 'モヤシ',
    'にら': 'ニラ',
    'ニラ': 'ニラ',
    '白ねぎ': 'ネギ',
    '白葱': 'ネギ',
    'おしゃれ葱': 'ネギ',
    'ねぎ': 'ネギ',
    '長芋': 'ナガイモ',
    '大和芋': 'ヤマトイモ',
    '里芋': 'サトイモ',
    '甘藷': 'サツマイモ',
    '馬鈴薯': 'ジャガイモ',
    '男爵': 'ジャガイモ',
    '新じゃが': 'ジャガイモ',
    '生姜': 'ショウガ',
    '蓮根': 'レンコン',
    '茗荷': 'ミョウガ',
    '玉葱': 'タマネギ',
    '長茄子': 'ナス',
    '茄子 AL': 'ナス',
    '茄子2L（Ｌ）': 'ナス',
    '茄子2L': 'ナス',
    'オクラ': 'オクラ',
    'ズッキーニ': 'ズッキーニ',
    'ゴーヤ': 'ゴーヤ',
    'ベビーコーン': 'トウモロコシ',
    'スナックえんどう': 'エンドウ',
    'キヌサヤ': 'エンドウ',
    'インゲン': 'インゲン',
    'セルリー': 'セロリ',
    'カリフラワー': 'カリフラワー',
    'アスパラ': 'アスパラガス',
    'アスパラガス': 'アスパラガス',
    'なめこ': 'ナメコ',
    'エノキ': 'エノキ',
    'えのき': 'エノキ',
    'えのき茸': 'エノキ',
    'エリンギ': 'エリンギ',
    'エリンギ（ホクト）': 'エリンギ',
    'マイタケ': 'マイタケ',
    '舞茸': 'マイタケ',
    '舞茸（ホクト）': 'マイタケ',
    '本シメジ': 'シメジ',
    'ぶなしめじ': 'ブナシメジ',
    '生椎茸': 'シイタケ',
    '生椎茸 小': 'シイタケ',
    '生椎茸　８枚': 'シイタケ',
    'りんご': 'リンゴ',
    'りんご（加工用）': 'リンゴ',
    'りんご（サラダ用）': 'リンゴ',
    'オレンジ': 'オレンジ',
    'キウイ': 'キウイ',
    'レモン': 'レモン',
    '苺': 'イチゴ',
    'バナナ': 'バナナ',
    'グレープフルーツ': 'グレープフルーツ',
    'グレープフルーツ（ホワイト）': 'グレープフルーツ',
    'グレープフルーツ（ルビー）': 'グレープフルーツ',
    'ハネジューメロン': 'メロン',
    '梨': 'ナシ',
    'アーリーレッド': 'トマト',
    '赤パプリカ': 'パプリカ',
    '黄色パプリカ': 'パプリカ',
    'レッドオニオン': 'タマネギ',
    'レッドキャベツ': 'キャベツ',
    '大玉キャベツ': 'キャベツ',
    '減農園きゅうり': 'キュウリ',
    '漬物用きゅうり': 'キュウリ',
    'サラダ水菜': 'ミズナ',
    'スペアミント': 'ミント',
    '剥き玉ねぎ': 'タマネギ',
    '皮付き人参': 'ニンジン',
    '皮付き玉ねぎ': 'タマネギ',
    '茄子': 'ナス',
}

def get_unified_name(product_name, mapping):
    """品名から統一品名（カタカナ）を取得"""
    product_name = str(product_name).strip()
    
    # 直接マッピング（最優先）
    if product_name in mapping:
        unified = mapping[product_name]
        if unified is not None:
            return unified
    
    # 部分一致（長いキーから順に検索）
    sorted_keys = sorted([k for k in mapping.keys() if mapping[k] is not None], 
                        key=len, reverse=True)
    for key in sorted_keys:
        value = mapping[key]
        if key in product_name:
            return value
    
    # 逆方向の部分一致
    for key, value in mapping.items():
        if value is not None and product_name in key:
            return value
    
    return None

def extract_vendor_and_date_from_filename(filename):
    """Extract vendor and date from filename"""
    name_without_ext = filename.rsplit('.', 1)[0]
    
    if '_' not in name_without_ext:
        return None, None, f"❌ エラー: ファイル名にアンダースコア（_）が含まれていません。\n正しい形式: `取引先名_YYYY_MM_DD.csv`"
    
    parts = name_without_ext.split('_', 1)
    if len(parts) < 2:
        return None, None, f"❌ エラー: ファイル名の形式が正しくありません。\n正しい形式: `取引先名_YYYY_MM_DD.csv`"
    
    vendor_part = parts[0].strip()
    date_part = parts[1]
    
    vendor = None
    vendor_part_normalized = vendor_part.strip()
    
    # First try exact match
    if vendor_part_normalized in SUPPORTED_VENDORS:
        vendor = vendor_part_normalized
    else:
        # Try matching with each supported vendor
        for v in SUPPORTED_VENDORS:
            v_normalized = v.strip()
            # Exact match
            if v_normalized == vendor_part_normalized:
                vendor = v
                break
            # Check if vendor name is in the filename part
            elif v_normalized in vendor_part_normalized:
                vendor = v
                break
            # Check if filename part is in vendor name
            elif vendor_part_normalized in v_normalized:
                vendor = v
                break
            # Byte-level comparison for encoding issues
            elif vendor_part_normalized.encode('utf-8') == v_normalized.encode('utf-8'):
                vendor = v
                break
    
    date_str = None
    error_msg = None
    
    date_match = re.search(r'(\d{4})_(\d{1,2})_(\d{1,2})', date_part)
    if date_match:
        year, month, day = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
        try:
            date_obj = datetime(year, month, day)
            if date_obj.weekday() != 0:
                error_msg = f"❌ エラー: ファイル名の日付は月曜日である必要があります。\n指定された日付: {year}/{month:02d}/{day:02d}"
            else:
                date_str = f"{year}/{month:02d}/{day:02d}"
        except ValueError:
            error_msg = f"❌ エラー: 無効な日付です。"
    else:
        error_msg = f"❌ エラー: ファイル名に日付が含まれていません。\n正しい形式: `取引先名_YYYY_MM_DD.csv`"
    
    return vendor, date_str, error_msg

def parse_kg_price(price_str):
    """Parse kg price from various formats"""
    if pd.isna(price_str) or price_str == '' or price_str == '×' or str(price_str).startswith('#'):
        return None
    price_str = str(price_str).strip()
    if 'PK' in price_str or '円' in price_str:
        numbers = re.findall(r'[\d,]+\.?\d*', price_str.replace(',', ''))
        if numbers:
            try:
                return float(numbers[0])
            except:
                pass
    cleaned = re.sub(r'[^\d.]', '', price_str.replace(',', ''))
    if cleaned:
        try:
            return float(cleaned)
        except:
            pass
    return None

def extract_maruei_products(df, week):
    """Extract products from マルエイ"""
    header_row = None
    for i in range(len(df)):
        row_str = ' '.join([str(x) for x in df.iloc[i].values if pd.notna(x)])
        if '品名' in row_str:
            header_row = i
            break
    
    if header_row is None:
        return []
    
    products = []
    supplier = 'マルエイ'
    
    for i in range(header_row + 2, len(df)):
        row = df.iloc[i]
        if len(row) > 1 and pd.notna(row.iloc[1]):
            product_name = str(row.iloc[1]).strip()
            if not product_name or product_name == '' or product_name == 'nan':
                continue
            
            origin = str(row.iloc[2]).strip() if len(row) > 2 and pd.notna(row.iloc[2]) else ''
            kg_price = None
            for col_idx in [12, 13, 14]:
                if len(row) > col_idx and pd.notna(row.iloc[col_idx]):
                    price_val = row.iloc[col_idx]
                    kg_price = parse_kg_price(price_val)
                    if kg_price is not None:
                        break
            
            if kg_price is not None:
                unified_name = get_unified_name(product_name, UNIFIED_NAME_MAPPING)
                products.append({
                    '品名': product_name,
                    '統一品名（カタカナ）': unified_name if unified_name else '未マッピング',
                    '取引先': supplier,
                    '産地': origin,
                    'kg単価': kg_price,
                    'その週': week
                })
    
    return products

def extract_hamamatsu_products(df, week):
    """Extract products from 浜松ベジタブル"""
    header_row = None
    for i in range(len(df)):
        row_str = ' '.join([str(x) for x in df.iloc[i].values if pd.notna(x)])
        if '商品名' in row_str and '産地' in row_str:
            header_row = i
            break
    
    if header_row is None:
        return []
    
    products = []
    supplier = '浜松ベジタブル'
    
    for i in range(header_row + 1, len(df)):
        row = df.iloc[i]
        if pd.notna(row.iloc[0]):
            product_name = str(row.iloc[0]).strip()
            if not product_name or product_name == '' or product_name == 'nan':
                continue
            if 'TEL' in product_name or 'FAX' in product_name:
                continue
            
            origin = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
            kg_price = None
            if len(row) > 6 and pd.notna(row.iloc[6]):
                kg_price = parse_kg_price(row.iloc[6])
            
            if kg_price is not None:
                unified_name = get_unified_name(product_name, UNIFIED_NAME_MAPPING)
                products.append({
                    '品名': product_name,
                    '統一品名（カタカナ）': unified_name if unified_name else '未マッピング',
                    '取引先': supplier,
                    '産地': origin,
                    'kg単価': kg_price,
                    'その週': week
                })
    
    return products

def extract_aguri_products(df, week):
    """Extract products from アグリ"""
    products = []
    supplier = 'アグリ'
    
    for i in range(3, len(df)):
        if len(df.columns) > 2:
            product_name = str(df.iloc[i, 2])
            if pd.notna(product_name):
                product_name = product_name.replace('　', '').replace(' ', '').strip()
                if product_name and product_name != 'nan' and '商品' not in product_name:
                    origin = str(df.iloc[i, 3]).strip() if len(df.columns) > 3 and pd.notna(df.iloc[i, 3]) else ''
                    kg_price = None
                    if len(df.columns) > 6 and pd.notna(df.iloc[i, 6]):
                        kg_price = parse_kg_price(df.iloc[i, 6])
                    
                    if kg_price is not None:
                        unified_name = get_unified_name(product_name, UNIFIED_NAME_MAPPING)
                        products.append({
                            '品名': product_name,
                            '統一品名（カタカナ）': unified_name if unified_name else '未マッピング',
                            '取引先': supplier,
                            '産地': origin,
                            'kg単価': kg_price,
                            'その週': week
                        })
    
    return products

def extract_date_from_aguri_header(df):
    """Extract date from アグリ CSV header"""
    for i in range(min(5, len(df))):
        row_str = ' '.join([str(x) for x in df.iloc[i].values if pd.notna(x)])
        date_match = re.search(r'(\d{1,2})月(\d{1,2})日', row_str)
        if date_match:
            month = int(date_match.group(1))
            day = int(date_match.group(2))
            current_year = datetime.now().year
            try:
                date_obj = datetime(current_year, month, day)
                weekday = date_obj.weekday()
                if weekday == 0:
                    monday_date = date_obj
                else:
                    days_until_next_monday = 7 - weekday
                    monday_date = date_obj + timedelta(days=days_until_next_monday)
                return f"{monday_date.year}/{monday_date.month:02d}/{monday_date.day:02d}"
            except:
                pass
    return None

# File upload
st.header("📁 CSVファイルアップロード")

st.info("💡 **一度に1つのファイルをアップロードしてください。**\n\n対応取引先: " + ", ".join(SUPPORTED_VENDORS))

uploaded_file = st.file_uploader(
    "CSVファイルをアップロード（1ファイルのみ）", 
    type=['csv'],
    help="ファイル名形式: 取引先名_YYYY_MM_DD.csv (例: マルエイ_2025_12_22.csv)"
)

if uploaded_file:
    vendor, date_from_filename, date_error = extract_vendor_and_date_from_filename(uploaded_file.name)
    
    st.info(f"📄 ファイル名: {uploaded_file.name}")
    
    if not vendor:
        st.error(f"❌ サポートされていない取引先です。")
        st.info(f"**対応取引先:** {', '.join(SUPPORTED_VENDORS)}")
        st.stop()
    
    if date_error:
        st.error(date_error)
        st.stop()
    
    if date_from_filename:
        st.success(f"✓ 取引先: {vendor}")
        st.success(f"✓ 日付: {date_from_filename} (月曜日 ✓)")
    
    if st.button("🔄 データを整理", type="primary"):
        try:
            with st.spinner("データを処理中..."):
                def read_csv_with_encoding(file, encodings=['utf-8', 'utf-8-sig', 'shift_jis', 'cp932', 'euc-jp']):
                    file.seek(0)
                    content = file.read()
                    if isinstance(content, str):
                        content = content.encode('utf-8')
                    for encoding in encodings:
                        try:
                            decoded_content = content.decode(encoding, errors='ignore')
                            return pd.read_csv(StringIO(decoded_content), header=None, on_bad_lines='skip', engine='python')
                        except:
                            continue
                    decoded_content = content.decode('utf-8', errors='ignore')
                    return pd.read_csv(StringIO(decoded_content), header=None, on_bad_lines='skip', engine='python')
                
                df = read_csv_with_encoding(uploaded_file)
                
                week = date_from_filename
                if not week and vendor == 'アグリ':
                    week = extract_date_from_aguri_header(df)
                
                if not week:
                    st.error("❌ 日付が抽出できませんでした")
                    st.stop()
                
                products = []
                if vendor == 'マルエイ':
                    products = extract_maruei_products(df, week)
                elif vendor == '浜松ベジタブル':
                    products = extract_hamamatsu_products(df, week)
                elif vendor == 'アグリ':
                    products = extract_aguri_products(df, week)
                elif vendor == 'おやさい':
                    st.warning(f"⚠️ {vendor}の抽出ロジックはまだ実装されていません。")
                    products = []
                
                if len(products) == 0:
                    st.error("❌ データが抽出されませんでした。")
                else:
                    df_consolidated = pd.DataFrame(products)
                    df_consolidated = df_consolidated[['品名', '統一品名（カタカナ）', '取引先', '産地', 'kg単価', 'その週']]
                    df_consolidated = df_consolidated.sort_values(['その週', '統一品名（カタカナ）', '品名', '取引先'])
                    
                    # Check for unmapped products
                    unmapped = df_consolidated[df_consolidated['統一品名（カタカナ）'] == '未マッピング']
                    if len(unmapped) > 0:
                        st.warning(f"⚠️ **警告: {len(unmapped)}件の品名がマッピングされていません:**")
                        unmapped_products = unmapped['品名'].unique()
                        for product in unmapped_products:
                            st.warning(f"  - {product}")
                    
                    st.success(f"✓ データ整理完了！ {len(df_consolidated)}件のデータ")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("データ数", len(df_consolidated))
                    with col2:
                        st.metric("取引先", vendor)
                    with col3:
                        st.metric("週", week)
                    
                    st.subheader("📋 コピー&ペースト用データ")
                    output_text = df_consolidated.to_csv(sep='\t', index=False, encoding='utf-8-sig')
                    st.code(output_text, language=None)
                    
                    st.subheader("📊 データプレビュー")
                    st.dataframe(df_consolidated, use_container_width=True)
                    
        except Exception as e:
            st.error(f"❌ エラーが発生しました: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

