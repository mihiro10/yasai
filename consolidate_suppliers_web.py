#!/usr/bin/env python3
"""
Web-based version of consolidate_suppliers using Streamlit.
User can upload CSV files through browser and download consolidated file.
"""
import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="野菜価格統合ツール", layout="wide")

st.title("🥬 野菜価格統合ツール")
st.markdown("取引先のCSVファイルを統合して、分析用のファイルを作成します。")

def extract_date_from_header(df, supplier_name):
    """Extract Monday date from the date range in CSV header"""
    for i in range(min(5, len(df))):
        row_str = ' '.join([str(x) for x in df.iloc[i].values if pd.notna(x)])
        date_match = re.search(r'(\d{1,2})/(\d{1,2})', row_str)
        if date_match:
            month = int(date_match.group(1))
            day = int(date_match.group(2))
            try:
                date_obj = datetime(2025, month, day)
                weekday = date_obj.weekday()
                if weekday == 0:
                    monday_date = date_obj
                else:
                    days_until_next_monday = 7 - weekday
                    monday_date = date_obj + timedelta(days=days_until_next_monday)
                return f"{monday_date.year}/{monday_date.month:02d}/{monday_date.day:02d}"
            except:
                return f"2025/{month:02d}/{day:02d}"
    return None

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

def extract_hamamatsu_products(df):
    """Extract products from 浜松ベジタブル単価表.csv"""
    week = extract_date_from_header(df, '浜松ベジタブル')
    if not week:
        week = '12/22～1/11'
    
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

def extract_maruei_products(df):
    """Extract products from マルエイ市況.csv"""
    week = extract_date_from_header(df, 'マルエイ')
    if not week:
        week = '12/19(金)～12/25(木)'
    
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
            if len(row) > 12 and pd.notna(row.iloc[12]):
                kg_price = parse_kg_price(row.iloc[12])
            
            if kg_price is not None:
                products.append({
                    '品名': product_name,
                    '取引先': supplier,
                    '産地': origin,
                    'kg単価': kg_price,
                    'その週': week
                })
    
    return products

# File upload section
st.header("📁 ファイルアップロード")

col1, col2 = st.columns(2)

with col1:
    maruei_file = st.file_uploader("マルエイ市況.csv", type=['csv'], key='maruei')
    if maruei_file:
        st.success(f"✓ {maruei_file.name} アップロード済み")

with col2:
    hamamatsu_file = st.file_uploader("浜松ベジタブル単価表.csv", type=['csv'], key='hamamatsu')
    if hamamatsu_file:
        st.success(f"✓ {hamamatsu_file.name} アップロード済み")

# Process button
if st.button("🔄 統合実行", type="primary"):
    if maruei_file and hamamatsu_file:
        try:
            with st.spinner("データを処理中..."):
                # Read CSV files with multiple encoding support
                def read_csv_with_encoding(file, encodings=['utf-8', 'utf-8-sig', 'shift_jis', 'cp932', 'euc-jp']):
                    for encoding in encodings:
                        try:
                            file.seek(0)  # Reset file pointer
                            return pd.read_csv(file, header=None, encoding=encoding)
                        except (UnicodeDecodeError, UnicodeError):
                            continue
                    # If all encodings fail, try with errors='ignore'
                    file.seek(0)
                    return pd.read_csv(file, header=None, encoding='utf-8', errors='ignore')
                
                df_maruei = read_csv_with_encoding(maruei_file)
                df_hamamatsu = read_csv_with_encoding(hamamatsu_file)
                
                # Extract products
                maruei_products = extract_maruei_products(df_maruei)
                hamamatsu_products = extract_hamamatsu_products(df_hamamatsu)
                
                # Combine
                all_products = maruei_products + hamamatsu_products
                df_consolidated = pd.DataFrame(all_products)
                df_consolidated = df_consolidated[['品名', '取引先', '産地', 'kg単価', 'その週']]
                df_consolidated = df_consolidated.sort_values(['その週', '品名', '取引先'])
                
                st.success(f"✓ 統合完了！ {len(df_consolidated)}件のデータ")
                
                # Display summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("総データ数", len(df_consolidated))
                with col2:
                    st.metric("取引先数", df_consolidated['取引先'].nunique())
                with col3:
                    st.metric("商品数", df_consolidated['品名'].nunique())
                
                # Show preview
                st.subheader("📊 プレビュー（最初の20行）")
                st.dataframe(df_consolidated.head(20), use_container_width=True)
                
                # Download buttons
                st.subheader("💾 ダウンロード")
                
                # CSV download
                csv_buffer = io.StringIO()
                df_consolidated.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📄 CSV形式でダウンロード",
                    data=csv_buffer.getvalue(),
                    file_name="統合_野菜価格.csv",
                    mime="text/csv"
                )
                
                # Excel download
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df_consolidated.to_excel(writer, index=False, sheet_name='統合データ')
                st.download_button(
                    label="📊 Excel形式でダウンロード",
                    data=excel_buffer.getvalue(),
                    file_name="統合_野菜価格.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")
            st.exception(e)
    else:
        st.warning("⚠️ 両方のCSVファイルをアップロードしてください。")

# Instructions
with st.expander("📖 使い方"):
    st.markdown("""
    1. 上記のファイルアップロード欄から、2つのCSVファイルをアップロードします
    2. 「統合実行」ボタンをクリックします
    3. 処理が完了したら、CSVまたはExcel形式でダウンロードできます
    
    **必要なファイル:**
    - マルエイ市況.csv
    - 浜松ベジタブル単価表.csv
    """)

