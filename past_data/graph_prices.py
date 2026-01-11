#!/usr/bin/env python3
"""
Graph price trends over time for vegetables.
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os

# Set Japanese font for matplotlib
plt.rcParams['font.family'] = 'DejaVu Sans'
# For better Japanese support, you might need to install and use a Japanese font
# plt.rcParams['font.family'] = 'Hiragino Sans'

def graph_product(product_name, data_file='past_data/統合_野菜価格_過去データ.csv'):
    """Graph price trends for a specific product"""
    
    # Read data
    df = pd.read_csv(data_file, encoding='utf-8-sig')
    
    # Filter for the product
    product_data = df[df['品名'] == product_name].copy()
    
    if len(product_data) == 0:
        print(f"No data found for {product_name}")
        return
    
    # Convert その週 to datetime
    product_data['その週_datetime'] = pd.to_datetime(product_data['その週'], format='%Y/%m/%d')
    
    # Sort by date
    product_data = product_data.sort_values(['その週_datetime', '取引先'])
    
    # Create the graph
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot each supplier as a separate line
    suppliers = product_data['取引先'].unique()
    colors = plt.cm.tab10(range(len(suppliers)))
    
    for supplier, color in zip(suppliers, colors):
        supplier_data = product_data[product_data['取引先'] == supplier]
        ax.plot(supplier_data['その週_datetime'], 
                supplier_data['kg単価'], 
                marker='o', 
                label=supplier, 
                linewidth=2,
                markersize=6,
                color=color)
    
    # Formatting
    ax.set_xlabel('週 (Week)', fontsize=12)
    ax.set_ylabel('kg単価 (Price per kg)', fontsize=12)
    ax.set_title(f'{product_name} 価格推移 (Price Trends)', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m/%d'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    plt.xticks(rotation=45, ha='right')
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the graph
    output_file = f'graph_{product_name}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Graph saved to: {output_file}")
    
    # Also save as PDF for better quality
    output_pdf = f'graph_{product_name}.pdf'
    plt.savefig(output_pdf, bbox_inches='tight')
    print(f"Graph saved to: {output_pdf}")
    
    # Don't show interactively (comment out if you want to see it)
    # plt.show()
    plt.close()
    
    # Print summary
    print(f"\n{product_name} - Price Summary:")
    print("=" * 60)
    for supplier in suppliers:
        supplier_data = product_data[product_data['取引先'] == supplier]
        print(f"\n{supplier}:")
        print(f"  Min: {supplier_data['kg単価'].min():.0f}円")
        print(f"  Max: {supplier_data['kg単価'].max():.0f}円")
        print(f"  Avg: {supplier_data['kg単価'].mean():.0f}円")
        print(f"  Latest: {supplier_data.iloc[-1]['kg単価']:.0f}円 ({supplier_data.iloc[-1]['その週']})")

if __name__ == "__main__":
    graph_product('ごぼう')

