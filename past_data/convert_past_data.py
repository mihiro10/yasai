#!/usr/bin/env python3
"""
Convert past_data/野菜週間価格.xlsx to 統合_野菜価格 format.
Extracts: 品名, 取引先, 産地, kg単価, その週
"""
import pandas as pd
import re
from datetime import datetime, timedelta

def extract_supplier_from_product_name(product_name):
    """Extract supplier name from product name like 'ごぼう（マルエイ）'"""
    # Look for pattern like （マルエイ）or （おやさい）
    match = re.search(r'（([^）]+)）', product_name)
    if match:
        return match.group(1)
    return None

def clean_product_name(product_name):
    """Remove supplier and other annotations from product name"""
    # Remove supplier in parentheses
    product_name = re.sub(r'（[^）]+）', '', product_name)
    # Remove other annotations like ※契約
    product_name = re.sub(r'※[^　]*', '', product_name)
    product_name = re.sub(r'\s+', '', product_name)
    return product_name.strip()

def parse_price(price_str):
    """Parse price from string, handling '-' and other formats"""
    if pd.isna(price_str) or price_str == '' or price_str == '-' or str(price_str).startswith('#'):
        return None
    
    price_str = str(price_str).strip()
    # Remove non-numeric characters except decimal point
    cleaned = re.sub(r'[^\d.]', '', price_str.replace(',', ''))
    if cleaned:
        try:
            return float(cleaned)
        except:
            pass
    return None

def convert_past_data():
    """Convert past_data Excel file to 統合_野菜価格 format"""
    
    file_path = 'past_data/野菜週間価格.xlsx'
    print(f"Reading {file_path}...")
    df = pd.read_excel(file_path, header=None)
    
    # Find header row (row with 品名 and dates)
    header_row = None
    for i in range(min(10, len(df))):
        row_str = ' '.join([str(x) for x in df.iloc[i].values if pd.notna(x)])
        if '品名' in row_str and '産地' in row_str:
            header_row = i
            break
    
    if header_row is None:
        print("Error: Could not find header row")
        return None
    
    print(f"Found header at row {header_row}")
    
    # Extract dates from header row
    dates = []
    date_columns = []  # Store column indices for dates
    price_columns = []  # Store column indices for prices
    
    header_row_data = df.iloc[header_row]
    for col_idx in range(len(header_row_data)):
        val = header_row_data.iloc[col_idx]
        if pd.notna(val):
            val_str = str(val)
            # Check if it's a date
            if '2025' in val_str or '2024' in val_str:
                try:
                    # Try to parse as date
                    if isinstance(val, datetime):
                        date_obj = val
                    else:
                        date_obj = pd.to_datetime(val_str)
                    
                    # Format as YYYY/MM/DD (Monday of that week)
                    weekday = date_obj.weekday()  # 0=Monday
                    if weekday == 0:
                        monday_date = date_obj
                    else:
                        days_until_next_monday = 7 - weekday
                        monday_date = date_obj + timedelta(days=days_until_next_monday)
                    
                    date_str = f"{monday_date.year}/{monday_date.month:02d}/{monday_date.day:02d}"
                    dates.append(date_str)
                    date_columns.append(col_idx)
                    # Price is in the same column as the date (in data rows)
                    price_columns.append(col_idx)
                except:
                    pass
    
    print(f"Found {len(dates)} weeks: {dates}")
    
    # Extract products
    products = []
    
    for i in range(header_row + 1, len(df)):
        row = df.iloc[i]
        
        # Check if row has product data
        if pd.notna(row.iloc[0]):  # 品名 column
            product_full_name = str(row.iloc[0]).strip()
            
            # Skip empty rows and reference rows
            if not product_full_name or product_full_name == '' or product_full_name == 'nan':
                continue
            if '【参考】' in product_full_name or '過去3週' in product_full_name:
                continue
            
            # Extract supplier and clean product name
            supplier = extract_supplier_from_product_name(product_full_name)
            if not supplier:
                # Skip rows without supplier (like reference price rows)
                continue
            
            product_name = clean_product_name(product_full_name)
            origin = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
            
            # Extract prices for each week
            for date_idx, date_str in enumerate(dates):
                price_col = price_columns[date_idx]
                
                if price_col < len(row):
                    price = parse_price(row.iloc[price_col])
                    
                    if price is not None:
                        products.append({
                            '品名': product_name,
                            '取引先': supplier,
                            '産地': origin,
                            'kg単価': price,
                            'その週': date_str
                        })
    
    # Create DataFrame
    df_output = pd.DataFrame(products)
    
    # Reorder columns
    df_output = df_output[['品名', '取引先', '産地', 'kg単価', 'その週']]
    
    # Sort by week first, then product name and supplier (for weekly updates)
    df_output = df_output.sort_values(['その週', '品名', '取引先'])
    
    # Save to CSV
    output_csv = 'past_data/統合_野菜価格_過去データ.csv'
    df_output.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"\nSaved to: {output_csv}")
    
    # Also save to Excel
    output_xlsx = 'past_data/統合_野菜価格_過去データ.xlsx'
    df_output.to_excel(output_xlsx, index=False, engine='openpyxl')
    print(f"Saved to: {output_xlsx}")
    
    print(f"\nTotal products: {len(df_output)}")
    print(f"Unique products: {df_output['品名'].nunique()}")
    print(f"Unique suppliers: {df_output['取引先'].unique()}")
    print(f"Date range: {df_output['その週'].min()} to {df_output['その週'].max()}")
    
    print(f"\nFirst 15 rows:")
    print(df_output.head(15).to_string(index=False))
    
    return df_output

if __name__ == "__main__":
    convert_past_data()

