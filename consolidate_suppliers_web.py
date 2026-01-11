#!/usr/bin/env python3
"""
Web-based vegetable price consolidator - Version 2
Based on flowchart: Excel file → Extract from filename → Process 4 vendors → Copy-paste format
"""
import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="野菜価格統合ツール", layout="wide")

st.title("🥬 野菜価格統合ツール")
st.markdown("Excelファイルをアップロードして、データを自動で整理します。")

# Supported vendors (4 vendors)
SUPPORTED_VENDORS = ['マルエイ', '浜松ベジタブル', 'おやさい', 'アグリ']

def extract_vendor_and_date_from_filename(filename):
    """
    Extract vendor name and date from filename.
    Format must be: vendor_YYYY-MM-DD.xlsx (underscore required)
    Date must be a Monday.
    Returns: (vendor, date_str, error_message)
    """
    # Remove extension
    name_without_ext = filename.rsplit('.', 1)[0]
    
    # Check for underscore
    if '_' not in name_without_ext:
        return None, None, f"❌ エラー: ファイル名にアンダースコア（_）が含まれていません。\n現在のファイル名: {filename}\n正しい形式: `取引先名_YYYY_MM_DD.csv`\n例: `マルエイ_2025_12_22.csv`"
    
    # Split by underscore
    parts = name_without_ext.split('_', 1)
    if len(parts) < 2:
        return None, None, f"❌ エラー: ファイル名の形式が正しくありません。\n現在のファイル名: {filename}\n正しい形式: `取引先名_YYYY_MM_DD.csv`\n例: `マルエイ_2025_12_22.csv`"
    
    vendor_part = parts[0].strip()
    date_part = parts[1]
    
    # Try to find vendor name - check for exact match first, then substring match
    vendor = None
    # First try exact match
    if vendor_part in SUPPORTED_VENDORS:
        vendor = vendor_part
    else:
        # Then try substring match
        for v in SUPPORTED_VENDORS:
            if v in vendor_part or vendor_part in v:
                vendor = v
                break
    
    # Try to find date - ONLY accept YYYY_MM_DD format (underscore separated)
    date_str = None
    error_msg = None
    
    # Try YYYY_MM_DD format (underscore separated)
    date_match = re.search(r'(\d{4})_(\d{1,2})_(\d{1,2})', date_part)
    if date_match:
        year, month, day = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
        try:
            date_obj = datetime(year, month, day)
            # Check if it's a Monday (weekday() returns 0 for Monday)
            if date_obj.weekday() != 0:
                error_msg = f"❌ エラー: ファイル名の日付は月曜日である必要があります。\n指定された日付: {year}/{month:02d}/{day:02d} ({['月', '火', '水', '木', '金', '土', '日'][date_obj.weekday()]}曜日)\n正しい形式の例: {vendor or '取引先名'}_2025_12_22.csv (月曜日)"
            else:
                date_str = f"{year}/{month:02d}/{day:02d}"
        except ValueError as e:
            error_msg = f"❌ エラー: 無効な日付です。\n指定された日付: {year}/{month:02d}/{day:02d}\n正しい形式の例: {vendor or '取引先名'}_2025_12_22.csv (YYYY_MM_DD形式、月曜日)"
    else:
        # No date found or wrong format
        error_msg = f"❌ エラー: ファイル名に日付が含まれていません、または形式が正しくありません。\n現在のファイル名: {filename}\nアンダースコア以降: {date_part}\n正しい形式の例: {vendor or '取引先名'}_2025_12_22.csv (YYYY_MM_DD形式、月曜日)"
    
    return vendor, date_str, error_msg

def extract_date_from_header(df, default_date):
    """Extract Monday date from the date range in CSV header"""
    current_year = datetime.now().year
    
    for i in range(min(5, len(df))):
        row_str = ' '.join([str(x) for x in df.iloc[i].values if pd.notna(x)])
        
        year_match = re.search(r'(\d{4})', row_str)
        if year_match:
            year = int(year_match.group(1))
        else:
            year = current_year
        
        date_match = re.search(r'(\d{1,2})/(\d{1,2})', row_str)
        if date_match:
            month = int(date_match.group(1))
            day = int(date_match.group(2))
            
            current_month = datetime.now().month
            if month <= 3 and current_month >= 10:
                year = current_year + 1
            elif month >= 10 and current_month <= 3:
                year = current_year - 1
            
            try:
                date_obj = datetime(year, month, day)
                weekday = date_obj.weekday()
                if weekday == 0:
                    monday_date = date_obj
                else:
                    days_until_next_monday = 7 - weekday
                    monday_date = date_obj + timedelta(days=days_until_next_monday)
                return f"{monday_date.year}/{monday_date.month:02d}/{monday_date.day:02d}"
            except ValueError:
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
                    return default_date
    return default_date

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
                products.append({
                    '品名': product_name,
                    '取引先': supplier,
                    '産地': origin,
                    'kg単価': kg_price,
                    'その週': week
                })
    
    return products

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
                products.append({
                    '品名': product_name,
                    '取引先': supplier,
                    '産地': origin,
                    'kg単価': kg_price,
                    'その週': week
                })
    
    return products

# File upload
st.header("📁 CSVファイルアップロード")

st.info("💡 **一度に1つのファイルをアップロードしてください。**\n\n対応取引先: " + ", ".join(SUPPORTED_VENDORS))

uploaded_file = st.file_uploader(
    "CSVファイルをアップロード（1ファイルのみ）", 
    type=['csv'],
    help="ファイル名形式: 取引先名_YYYY_MM_DD.csv (例: マルエイ_2025_12_22.csv)"
)

if uploaded_file:
    # Extract vendor and date from filename
    vendor, date_from_filename, date_error = extract_vendor_and_date_from_filename(uploaded_file.name)
    
    st.info(f"📄 ファイル名: {uploaded_file.name}")
    
    # Check for vendor
    if not vendor:
        st.error(f"❌ サポートされていない取引先です。")
        st.info(f"**対応取引先:** {', '.join(SUPPORTED_VENDORS)}")
        st.info(f"**ファイル名の形式:** `取引先名_YYYY_MM_DD.csv` (例: `マルエイ_2025_12_22.csv`)")
        st.info(f"**重要:** 日付は月曜日である必要があります。")
        st.stop()
    
    # Check for date error
    if date_error:
        st.error(date_error)
        st.stop()
    
    if date_from_filename:
        st.success(f"✓ 取引先: {vendor}")
        st.success(f"✓ 日付: {date_from_filename} (月曜日 ✓)")
    else:
        st.error("❌ 日付の抽出に失敗しました。")
        st.stop()
    
    # Process button
    if st.button("🔄 データを整理", type="primary"):
        try:
            with st.spinner("データを処理中..."):
                # Read CSV file with encoding support
                def read_csv_with_encoding(file, encodings=['utf-8', 'utf-8-sig', 'shift_jis', 'cp932', 'euc-jp']):
                    # Read file content as bytes
                    file.seek(0)
                    content = file.read()
                    
                    # If content is already a string, convert to bytes
                    if isinstance(content, str):
                        content = content.encode('utf-8')
                    
                    # Try each encoding
                    for encoding in encodings:
                        try:
                            decoded_content = content.decode(encoding, errors='ignore')
                            from io import StringIO
                            return pd.read_csv(StringIO(decoded_content), header=None, on_bad_lines='skip', engine='python')
                        except Exception:
                            continue
                    
                    # Last resort: force UTF-8 with ignore
                    decoded_content = content.decode('utf-8', errors='ignore')
                    from io import StringIO
                    return pd.read_csv(StringIO(decoded_content), header=None, on_bad_lines='skip', engine='python')
                
                df = read_csv_with_encoding(uploaded_file)
                
                # Use date from filename (already validated as Monday)
                week = date_from_filename
                
                # Extract products based on vendor
                products = []
                if vendor == 'マルエイ':
                    products = extract_maruei_products(df, week)
                elif vendor == '浜松ベジタブル':
                    products = extract_hamamatsu_products(df, week)
                elif vendor in ['おやさい', 'アグリ']:
                    # TODO: Implement extraction for おやさい and アグリ
                    st.warning(f"⚠️ {vendor}の抽出ロジックはまだ実装されていません。")
                    products = []
                
                if len(products) == 0:
                    st.error("❌ データが抽出されませんでした。ファイルの形式を確認してください。")
                else:
                    # Create DataFrame
                    df_consolidated = pd.DataFrame(products)
                    df_consolidated = df_consolidated[['品名', '取引先', '産地', 'kg単価', 'その週']]
                    df_consolidated = df_consolidated.sort_values(['その週', '品名', '取引先'])
                    
                    st.success(f"✓ データ整理完了！ {len(df_consolidated)}件のデータ")
                    
                    # Display summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("データ数", len(df_consolidated))
                    with col2:
                        st.metric("取引先", vendor)
                    with col3:
                        st.metric("週", week)
                    
                    # Copy-paste friendly format (tab-separated for Google Sheets)
                    st.subheader("📋 コピー&ペースト用データ")
                    st.markdown("以下のデータをコピーして、Google Sheetsに貼り付けてください。")
                    
                    # Create tab-separated text
                    output_text = df_consolidated.to_csv(sep='\t', index=False, encoding='utf-8-sig')
                    
                    # Display in text area for easy copying
                    st.text_area(
                        "コピー用データ（タブ区切り）",
                        output_text,
                        height=300,
                        help="このデータをコピーしてGoogle Sheetsに貼り付けてください"
                    )
                    
                    # Also show as table
                    st.subheader("📊 データプレビュー")
                    st.dataframe(df_consolidated, use_container_width=True)
                    
                    # Download buttons
                    st.subheader("💾 ダウンロード")
                    
                    # CSV download
                    csv_buffer = io.StringIO()
                    df_consolidated.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📄 CSV形式でダウンロード",
                        data=csv_buffer.getvalue(),
                        file_name=f"統合_{vendor}_{week.replace('/', '-')}.csv",
                        mime="text/csv"
                    )
                    
                    # Excel download
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        df_consolidated.to_excel(writer, index=False, sheet_name='統合データ')
                    st.download_button(
                        label="📊 Excel形式でダウンロード",
                        data=excel_buffer.getvalue(),
                        file_name=f"統合_{vendor}_{week.replace('/', '-')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")
            st.exception(e)

# Instructions
with st.expander("📖 使い方"):
    st.markdown("""
    ### ワークフロー:
    1. CSVファイルを準備
    2. ファイル名に取引先の名前と日付を入れる
       - 形式: `取引先名_YYYY_MM_DD.csv`
       - 例: `マルエイ_2025_12_22.csv`
    3. ファイルをアップロード
    4. 「データを整理」ボタンをクリック
    5. コピー&ペースト用データをコピー
    6. Google Sheetsに貼り付け
    
    ### 対応取引先:
    - マルエイ
    - 浜松ベジタブル
    - おやさい（準備中）
    - アグリ（準備中）
    
    ### ファイル名の形式（必須）:
    - **形式:** `取引先名_YYYY_MM_DD.csv`
    - **例:** `マルエイ_2025_12_22.csv`
    - **重要:** 
      - アンダースコア（_）で区切る
      - 日付は**YYYY_MM_DD**形式（アンダースコア区切り）
      - 日付は**月曜日**である必要があります
    - アンダースコアがない、月曜日でない、または形式が間違っている場合はエラーが表示されます
    """)

