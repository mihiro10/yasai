#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
野菜価格統合ツール（統一品名マッピング付き）
Streamlit Webアプリ
"""
import streamlit as st
import pandas as pd
import re
import unicodedata
import json
import os
import subprocess
from datetime import datetime, timedelta
from io import StringIO

st.set_page_config(page_title="野菜価格統合ツール", layout="wide")

# セッション状態の初期化（最初に実行する必要がある）
if 'product_mapping' not in st.session_state:
    # マッピングファイルのパス
    MAPPING_FILE = 'product_mapping.json'
    
    # デフォルトの統一品名マッピング辞書
    DEFAULT_UNIFIED_NAME_MAPPING = {
        'ごぼう': 'ゴボウ',
        'ゴボウ': 'ゴボウ',
        'ゴボウ（秋堀）': 'ゴボウ',
        'さつま芋': 'サツマイモ',
        'さつま芋2L': 'サツマイモ',
        '人参': 'ニンジン',
        '人参A2L': 'ニンジン',
        '人参B2L': 'ニンジン',
        '人参L': 'ニンジン',
        '人参L・2L': 'ニンジン',
        'にんじん': 'ニンジン',
        '大根': 'ダイコン',
        '玉ねぎ': 'タマネギ',
        '玉ねぎM・L・L大': 'タマネギ',
        'メークイン': 'ジャガイモ',
        'じゃがいも': 'ジャガイモ',
        'さやか': 'ジャガイモ',
        'キャベツ': 'キャベツ',
        '加工キャベツ': 'キャベツ',
        '紫キャベツ': 'ムラサキキャベツ',
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
        'キュウリ': 'キュウリ',
        '茄子L': 'ナス',
        '茄子優2L': 'ナス',
        '南瓜': 'カボチャ',
        'カボチャ': 'カボチャ',
        'かぼちゃ': 'カボチャ',
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
        '青ネギ': 'ネギ',
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
        'しいたけ　S': 'シイタケ',
        'しいたけ': 'シイタケ',
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
        '芯取り剥き玉': 'タマネギ',
        '茄子': 'ナス',
    }
    
    def load_mapping():
        """マッピング辞書をファイルから読み込む（存在しない場合はデフォルトを使用）"""
        if os.path.exists(MAPPING_FILE):
            try:
                with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return DEFAULT_UNIFIED_NAME_MAPPING.copy()
        return DEFAULT_UNIFIED_NAME_MAPPING.copy()
    
    st.session_state.product_mapping = load_mapping()
    st.session_state.mapping_file = MAPPING_FILE
    st.session_state.default_mapping = DEFAULT_UNIFIED_NAME_MAPPING

def save_mapping(mapping):
    """マッピング辞書をファイルに保存し、GitHubにコミット・プッシュ
    
    Returns:
        tuple: (success: bool, git_status_message: str)
    """
    mapping_file = st.session_state.get('mapping_file', 'product_mapping.json')
    try:
        # ファイルに保存
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        
        # GitHubにコミット・プッシュ（リポジトリに永続化）
        git_status = "ローカルに保存しました（Git操作はスキップされました）"
        try:
            # 現在のディレクトリを確認
            current_dir = os.getcwd()
            
            # Gitリポジトリか確認
            git_dir_check = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                capture_output=True,
                text=True,
                cwd=current_dir
            )
            
            if git_dir_check.returncode == 0:
                # Gitユーザー設定を確認・設定（リポジトリローカルのみ）
                user_name_check = subprocess.run(
                    ['git', 'config', 'user.name'],
                    capture_output=True,
                    text=True,
                    cwd=current_dir
                )
                if user_name_check.returncode != 0:
                    # ユーザー名が設定されていない場合は設定
                    subprocess.run(
                        ['git', 'config', 'user.name', 'Yasai App'],
                        capture_output=True,
                        text=True,
                        cwd=current_dir,
                        check=False
                    )
                
                user_email_check = subprocess.run(
                    ['git', 'config', 'user.email'],
                    capture_output=True,
                    text=True,
                    cwd=current_dir
                )
                if user_email_check.returncode != 0:
                    # メールアドレスが設定されていない場合は設定
                    subprocess.run(
                        ['git', 'config', 'user.email', 'yasai-app@streamlit.cloud'],
                        capture_output=True,
                        text=True,
                        cwd=current_dir,
                        check=False
                    )
                
                # ファイルをステージング（常に実行）
                add_result = subprocess.run(
                    ['git', 'add', mapping_file],
                    capture_output=True,
                    text=True,
                    cwd=current_dir,
                    check=False
                )
                
                # 変更があるか確認（HEADと比較）
                # HEADとステージングエリアの差分を確認
                diff_result = subprocess.run(
                    ['git', 'diff', '--cached', '--quiet', 'HEAD', '--', mapping_file],
                    capture_output=True,
                    text=True,
                    cwd=current_dir
                )
                
                # 戻り値が0の場合は変更なし、0以外の場合は変更あり
                has_changes = diff_result.returncode != 0
                    # コミット
                    commit_result = subprocess.run(
                        ['git', 'commit', '-m', f'Update product mapping: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'],
                        capture_output=True,
                        text=True,
                        cwd=current_dir
                    )
                    
                    if commit_result.returncode == 0:
                        # プッシュ（認証トークンを使用）
                        # Streamlit secretsからGitHubトークンを取得
                        github_token = None
                        try:
                            if hasattr(st, 'secrets') and 'GITHUB_TOKEN' in st.secrets:
                                github_token = st.secrets['GITHUB_TOKEN']
                        except:
                            pass
                        
                        # リモートURLを取得
                        remote_url_result = subprocess.run(
                            ['git', 'config', '--get', 'remote.origin.url'],
                            capture_output=True,
                            text=True,
                            cwd=current_dir
                        )
                        
                        if remote_url_result.returncode == 0 and github_token:
                            # HTTPS URLにトークンを埋め込む
                            remote_url = remote_url_result.stdout.strip()
                            if remote_url.startswith('https://'):
                                # https://github.com/user/repo.git -> https://token@github.com/user/repo.git
                                if '@' not in remote_url:
                                    remote_url = remote_url.replace('https://', f'https://{github_token}@')
                                    subprocess.run(
                                        ['git', 'remote', 'set-url', 'origin', remote_url],
                                        capture_output=True,
                                        text=True,
                                        cwd=current_dir,
                                        check=False
                                    )
                        
                        # プッシュ
                        push_result = subprocess.run(
                            ['git', 'push', 'origin', 'main'],
                            capture_output=True,
                            text=True,
                            cwd=current_dir,
                            check=False
                        )
                        if push_result.returncode == 0:
                            git_status = "✓ GitHubに正常にプッシュされました（永続化されました）"
                        else:
                            error_msg = push_result.stderr.strip() or push_result.stdout.strip() or '不明なエラー'
                            # 認証エラーの場合の特別なメッセージ
                            if 'Username' in error_msg or 'authentication' in error_msg.lower() or 'could not read' in error_msg.lower():
                                git_status = "⚠️ コミットは成功しましたが、プッシュに失敗しました（認証が必要です）。ファイルはローカルに保存されましたが、Streamlit Cloudの再起動時に失われる可能性があります。JSONファイルをダウンロードしてバックアップを取ることをお勧めします。"
                            else:
                                git_status = f"⚠️ コミットは成功しましたが、プッシュに失敗しました: {error_msg}"
                    else:
                        error_msg = commit_result.stderr.strip() or '不明なエラー'
                        git_status = f"⚠️ コミットに失敗しました: {error_msg}"
                else:
                    # 変更がない場合は既に最新
                    git_status = "✓ 変更はありません（既に最新の状態です）"
            else:
                git_status = "ローカルに保存しました（Gitリポジトリではありません）"
        except Exception as git_error:
            # Git操作が失敗してもファイル保存は成功とする
            git_status = f"ローカルに保存しました（Git操作エラー: {str(git_error)}）"
        
        return True, git_status
    except Exception as e:
        return False, f"保存エラー: {str(e)}"

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

# マッピング辞書の管理セクション
with st.expander("🔧 統一品名マッピング辞書の管理", expanded=False):
    st.markdown("""
    ### マッピング辞書について
    
    この辞書は、各取引先の品名を統一品名（カタカナ）にマッピングするために使用されます。
    
    - **左側（品名）**: 取引先のCSVファイルに記載されている実際の品名
    - **右側（統一品名）**: マッピング先の統一品名（カタカナ）
    
    新しい品名が追加された場合や、マッピングを変更したい場合は、このセクションで編集できます。
    """)
    
    # マッピングをDataFrameに変換
    mapping_data = []
    for product_name, unified_name in st.session_state.product_mapping.items():
        mapping_data.append({
            '品名': product_name,
            '統一品名（カタカナ）': unified_name if unified_name else '(未設定)'
        })
    
    mapping_df = pd.DataFrame(mapping_data)
    mapping_df = mapping_df.sort_values('品名')
    
    # 検索機能
    search_term = st.text_input("🔍 品名で検索", placeholder="例: かぼちゃ、トマト...")
    if search_term:
        filtered_df = mapping_df[mapping_df['品名'].str.contains(search_term, case=False, na=False) | 
                                 mapping_df['統一品名（カタカナ）'].str.contains(search_term, case=False, na=False)]
        st.dataframe(filtered_df, use_container_width=True, height=400)
        st.info(f"検索結果: {len(filtered_df)}件 / 全{len(mapping_df)}件")
    else:
        st.dataframe(mapping_df, use_container_width=True, height=400)
        st.info(f"全{len(mapping_df)}件のマッピング")
    
    st.markdown("---")
    st.subheader("➕ 新しいマッピングを追加")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        new_product_name = st.text_input("品名", placeholder="例: 新商品名", key="new_product")
    with col2:
        new_unified_name = st.text_input("統一品名（カタカナ）", placeholder="例: シンショウヒン", key="new_unified")
    with col3:
        st.write("")  # スペーサー
        add_button = st.button("追加", type="primary")
    
    if add_button:
        if new_product_name and new_unified_name:
            if new_product_name in st.session_state.product_mapping:
                st.error(f"❌ '{new_product_name}' は既に存在します。編集セクションで更新してください。")
            else:
                st.session_state.product_mapping[new_product_name] = new_unified_name
                success, git_status = save_mapping(st.session_state.product_mapping)
                if success:
                    st.success(f"✓ '{new_product_name}' → '{new_unified_name}' を追加しました")
                    st.info(git_status)
                    st.rerun()
        else:
            st.error("❌ 品名と統一品名の両方を入力してください")
    
    st.markdown("---")
    st.subheader("✏️ マッピングを編集・削除")
    
    # 編集用の選択
    edit_product_name = st.selectbox(
        "編集する品名を選択",
        options=sorted(st.session_state.product_mapping.keys()),
        key="edit_select"
    )
    
    if edit_product_name:
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.text_input("品名", value=edit_product_name, disabled=True, key="edit_product_display")
        with col2:
            current_unified = st.session_state.product_mapping[edit_product_name] or ''
            edited_unified = st.text_input("統一品名（カタカナ）", value=current_unified, key="edit_unified")
        with col3:
            st.write("")  # スペーサー
            col3_1, col3_2 = st.columns(2)
            with col3_1:
                update_button = st.button("更新", type="primary")
            with col3_2:
                delete_button = st.button("削除", type="secondary")
        
        if update_button:
            if edited_unified:
                st.session_state.product_mapping[edit_product_name] = edited_unified
                success, git_status = save_mapping(st.session_state.product_mapping)
                if success:
                    st.success(f"✓ '{edit_product_name}' のマッピングを更新しました")
                    st.info(git_status)
                    st.rerun()
            else:
                st.error("❌ 統一品名を入力してください（削除する場合は「削除」ボタンを使用）")
        
        if delete_button:
            confirm_key = f"confirm_delete_{edit_product_name}"
            if st.session_state.get(confirm_key, False):
                del st.session_state.product_mapping[edit_product_name]
                st.session_state[confirm_key] = False
                success, git_status = save_mapping(st.session_state.product_mapping)
                if success:
                    st.success(f"✓ '{edit_product_name}' を削除しました")
                    st.info(git_status)
                    st.rerun()
            else:
                st.session_state[confirm_key] = True
                st.warning(f"⚠️ 本当に '{edit_product_name}' を削除しますか？もう一度「削除」ボタンを押してください。")
    
    st.markdown("---")
    st.subheader("💾 マッピングの保存・復元")
    
    st.success("💾 **自動保存**: マッピングを保存すると、GitHubリポジトリに自動的にコミットされ、アプリが再起動しても永続的に保持されます。")
    
    st.markdown("""
    **📊 プッシュ状態の確認方法:**
    1. **アプリ内**: 保存後に表示される青い情報ボックスで確認
    2. **GitHub**: [リポジトリの `product_mapping.json`](https://github.com/mihiro10/yasai/blob/main/product_mapping.json) の更新日時を確認
    3. **コミット履歴**: [リポジトリのコミット履歴](https://github.com/mihiro10/yasai/commits/main/product_mapping.json) で最新のコミットを確認
    
    **⚠️ プッシュエラーについて:**
    変更を保存すると、ファイルはStreamlit Cloud環境内でローカルにコミットされます。ただし、GitHubへのプッシュには認証が必要です。
    
    **認証が必要な理由:** GitHubはリポジトリへの書き込み権限を確認するために認証情報を要求します。Streamlit Cloudはリポジトリを読み取ることはできますが、自動的に書き込み権限を持っているわけではありません。
    
    **現在の動作:** 変更はローカルに保存され、コミットされます。セッション中は保持されます。プッシュが失敗した場合：
    - JSONファイルをダウンロードしてバックアップを取ることができます
    - ローカルマシンから手動でプル/プッシュすれば、ローカルコミットが含まれます
    - または、Streamlit CloudでGitHub認証を設定することもできます（オプション）
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 変更を保存", type="primary"):
            success, git_status = save_mapping(st.session_state.product_mapping)
            if success:
                st.success("✓ マッピングを保存しました")
                st.info(git_status)
    with col2:
        # マッピングをダウンロード
        mapping_json = json.dumps(st.session_state.product_mapping, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 JSONでダウンロード",
            data=mapping_json,
            file_name="product_mapping.json",
            mime="application/json"
        )
    
    st.markdown("---")
    st.subheader("📤 保存したマッピングを復元")
    
    uploaded_mapping = st.file_uploader(
        "以前にダウンロードした `product_mapping.json` ファイルをアップロードして復元",
        type=['json'],
        key="mapping_upload"
    )
    
    if uploaded_mapping is not None:
        try:
            content = uploaded_mapping.read().decode('utf-8')
            restored_mapping = json.loads(content)
            
            if isinstance(restored_mapping, dict):
                st.success(f"✓ マッピングファイルを読み込みました（{len(restored_mapping)}件のエントリ）")
                st.json(restored_mapping)
                
                if st.button("🔄 このマッピングで上書き", type="primary"):
                    st.session_state.product_mapping = restored_mapping
                    success, git_status = save_mapping(st.session_state.product_mapping)
                    if success:
                        st.success("✓ マッピングを復元しました")
                        st.info(git_status)
                        st.rerun()
            else:
                st.error("❌ 無効なマッピングファイル形式です。JSONオブジェクト（辞書）である必要があります。")
        except json.JSONDecodeError:
            st.error("❌ JSONファイルの解析に失敗しました。正しいJSON形式のファイルをアップロードしてください。")
        except Exception as e:
            st.error(f"❌ エラー: {str(e)}")

# Supported vendors
SUPPORTED_VENDORS = ['マルエイ', '浜松ベジタブル', 'おやさい', 'アグリ']

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
    
    # Unicode normalization (NFC) to handle combining characters
    vendor_part_normalized = unicodedata.normalize('NFC', vendor_part_normalized)
    
    # Normalize both for comparison
    vendor_part_bytes = vendor_part_normalized.encode('utf-8')
    
    # First try exact match (string level) with normalized SUPPORTED_VENDORS
    normalized_supported = [unicodedata.normalize('NFC', v) for v in SUPPORTED_VENDORS]
    if vendor_part_normalized in normalized_supported:
        vendor = SUPPORTED_VENDORS[normalized_supported.index(vendor_part_normalized)]
    else:
        # Try matching with each supported vendor
        for v in SUPPORTED_VENDORS:
            v_normalized = unicodedata.normalize('NFC', v.strip())
            v_bytes = v_normalized.encode('utf-8')
            
            # Exact match (string) - both normalized
            if v_normalized == vendor_part_normalized:
                vendor = v
                break
            # Byte-level comparison (for encoding issues)
            elif vendor_part_bytes == v_bytes:
                vendor = v
                break
            # Check if vendor name is in the filename part (substring match)
            elif v_normalized in vendor_part_normalized:
                vendor = v
                break
            # Check if filename part is in vendor name (reverse substring)
            elif vendor_part_normalized in v_normalized:
                vendor = v
                break
            # Check for common prefix (浜松 for 浜松ベジタブル)
            elif len(v_normalized) >= 2 and len(vendor_part_normalized) >= 2:
                if v_normalized[:2] == vendor_part_normalized[:2] and v_normalized[:2] == '浜松':
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
    """
    Parse kg price from various formats
    Returns: (price_value, error_message)
    - price_value: float if valid, None if invalid
    - error_message: None if valid, error message if invalid
    """
    original_str = str(price_str) if pd.notna(price_str) else ''
    
    if pd.isna(price_str) or price_str == '':
        return None, None  # Empty is not an error, just skip
    
    price_str = str(price_str).strip()
    
    # Check for explicit error indicators
    if price_str == '×' or str(price_str).startswith('#'):
        return None, f"無効な価格値: '{original_str}'"
    
    # Check for non-numeric characters (excluding allowed ones)
    # Allowed: digits, comma, period, PK, 円
    allowed_pattern = r'[\d,.\sPK円@]'
    if not re.match(r'^[\d,.\sPK円@]+$', price_str.replace(',', '').replace(' ', '')):
        # Has invalid characters
        return None, f"価格に無効な文字が含まれています: '{original_str}'"
    
    # Try to extract number
    if 'PK' in price_str or '円' in price_str or '@' in price_str:
        numbers = re.findall(r'[\d,]+\.?\d*', price_str.replace(',', ''))
        if numbers:
            try:
                return float(numbers[0]), None
            except:
                return None, f"価格の解析に失敗しました: '{original_str}'"
    
    cleaned = re.sub(r'[^\d.]', '', price_str.replace(',', ''))
    if cleaned:
        try:
            return float(cleaned), None
        except:
            return None, f"価格の変換に失敗しました: '{original_str}'"
    
    return None, f"価格が抽出できませんでした: '{original_str}'"

def extract_maruei_products(df, week, mapping):
    """Extract products from マルエイ"""
    header_row = None
    for i in range(len(df)):
        row_str = ' '.join([str(x) for x in df.iloc[i].values if pd.notna(x)])
        if '品名' in row_str:
            header_row = i
            break
    
    if header_row is None:
        return [], []
    
    products = []
    price_errors = []
    supplier = 'マルエイ'
    
    for i in range(header_row + 2, len(df)):
        row = df.iloc[i]
        if len(row) > 1 and pd.notna(row.iloc[1]):
            product_name = str(row.iloc[1]).strip()
            if not product_name or product_name == '' or product_name == 'nan':
                continue
            
            origin = str(row.iloc[2]).strip() if len(row) > 2 and pd.notna(row.iloc[2]) else ''
            kg_price = None
            price_error = None
            
            for col_idx in [12, 13, 14]:
                if len(row) > col_idx and pd.notna(row.iloc[col_idx]):
                    price_val = row.iloc[col_idx]
                    kg_price, price_error = parse_kg_price(price_val)
                    if kg_price is not None:
                        break
                    elif price_error is not None:
                        # Store error but continue checking other columns
                        pass
            
            if kg_price is not None:
                unified_name = get_unified_name(product_name, mapping)
                products.append({
                    '品名': product_name,
                    '統一品名（カタカナ）': unified_name if unified_name else '未マッピング',
                    '取引先': supplier,
                    '産地': origin,
                    'kg単価': kg_price,
                    'その週': week
                })
            elif price_error is not None:
                # Record error for this product
                price_errors.append({
                    '品名': product_name,
                    '産地': origin,
                    'エラー': price_error,
                    '行番号': i + 1
                })
    
    return products, price_errors

def extract_hamamatsu_products(df, week, mapping):
    """Extract products from 浜松ベジタブル"""
    header_row = None
    for i in range(len(df)):
        row_str = ' '.join([str(x) for x in df.iloc[i].values if pd.notna(x)])
        if '商品名' in row_str and '産地' in row_str:
            header_row = i
            break
    
    if header_row is None:
        return [], []
    
    products = []
    price_errors = []
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
            price_error = None
            
            if len(row) > 6 and pd.notna(row.iloc[6]):
                kg_price, price_error = parse_kg_price(row.iloc[6])
            
            if kg_price is not None:
                unified_name = get_unified_name(product_name, mapping)
                products.append({
                    '品名': product_name,
                    '統一品名（カタカナ）': unified_name if unified_name else '未マッピング',
                    '取引先': supplier,
                    '産地': origin,
                    'kg単価': kg_price,
                    'その週': week
                })
            elif price_error is not None:
                price_errors.append({
                    '品名': product_name,
                    '産地': origin,
                    'エラー': price_error,
                    '行番号': i + 1
                })
    
    return products, price_errors

def extract_aguri_products(df, week, mapping):
    """Extract products from アグリ"""
    products = []
    price_errors = []
    supplier = 'アグリ'
    
    for i in range(3, len(df)):
        if len(df.columns) > 2:
            product_name = str(df.iloc[i, 2])
            if pd.notna(product_name):
                product_name = product_name.replace('　', '').replace(' ', '').strip()
                if product_name and product_name != 'nan' and '商品' not in product_name:
                    origin = str(df.iloc[i, 3]).strip() if len(df.columns) > 3 and pd.notna(df.iloc[i, 3]) else ''
                    kg_price = None
                    price_error = None
                    
                    if len(df.columns) > 6 and pd.notna(df.iloc[i, 6]):
                        kg_price, price_error = parse_kg_price(df.iloc[i, 6])
                    
                    if kg_price is not None:
                        unified_name = get_unified_name(product_name, mapping)
                        products.append({
                            '品名': product_name,
                            '統一品名（カタカナ）': unified_name if unified_name else '未マッピング',
                            '取引先': supplier,
                            '産地': origin,
                            'kg単価': kg_price,
                            'その週': week
                        })
                    elif price_error is not None:
                        price_errors.append({
                            '品名': product_name,
                            '産地': origin,
                            'エラー': price_error,
                            '行番号': i + 1
                        })
    
    return products, price_errors

def extract_oyasai_products(df, week, mapping):
    """Extract products from おやさい"""
    header_row = None
    for i in range(len(df)):
        row_str = ' '.join([str(x) for x in df.iloc[i].values if pd.notna(x)])
        if '商品番号・商品名' in row_str and '産地' in row_str and '単価kg' in row_str:
            header_row = i
            break
    
    if header_row is None:
        return [], []
    
    products = []
    price_errors = []
    supplier = 'おやさい'
    
    # Column indices based on the header:
    # 相場,商品番号・商品名,,,,産地,時期,規格,荷姿,単位,ロット/週,単価kg,1c/s 着価格
    # 0    1               5      6    7    8    9    10   11     12
    for i in range(header_row + 1, len(df)):
        row = df.iloc[i]
        if len(row) > 1 and pd.notna(row.iloc[1]):
            product_name = str(row.iloc[1]).strip()
            if not product_name or product_name == '' or product_name == 'nan':
                continue
            # Skip footer rows
            if '※' in product_name or 'お見積り' in product_name or '税別' in product_name:
                continue
            
            origin = str(row.iloc[5]).strip() if len(row) > 5 and pd.notna(row.iloc[5]) else ''
            kg_price = None
            price_error = None
            
            # 単価kg is in column 11 (index 11)
            if len(row) > 11 and pd.notna(row.iloc[11]):
                kg_price, price_error = parse_kg_price(row.iloc[11])
            
            if kg_price is not None:
                unified_name = get_unified_name(product_name, mapping)
                products.append({
                    '品名': product_name,
                    '統一品名（カタカナ）': unified_name if unified_name else '未マッピング',
                    '取引先': supplier,
                    '産地': origin,
                    'kg単価': kg_price,
                    'その週': week
                })
            elif price_error is not None:
                price_errors.append({
                    '品名': product_name,
                    '産地': origin,
                    'エラー': price_error,
                    '行番号': i + 1
                })
    
    return products, price_errors

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
        # Debug info
        if '_' in uploaded_file.name:
            parts = uploaded_file.name.rsplit('.', 1)[0].split('_', 1)
            detected_vendor_part = parts[0].strip() if len(parts) > 0 else ""
            st.warning(f"検出された取引先名部分: '{detected_vendor_part}'")
            st.warning(f"文字数: {len(detected_vendor_part)}文字")
            st.warning(f"バイト表現: {detected_vendor_part.encode('utf-8')}")
        st.info(f"**対応取引先:** {', '.join(SUPPORTED_VENDORS)}")
        st.info(f"**ファイル名の形式:** `取引先名_YYYY_MM_DD.csv` (例: `マルエイ_2025_12_22.csv`)")
        st.info(f"**重要:** 日付は月曜日である必要があります。")
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
                
                # 最新のマッピング辞書を取得
                current_mapping = st.session_state.product_mapping
                
                products = []
                price_errors = []
                if vendor == 'マルエイ':
                    products, price_errors = extract_maruei_products(df, week, current_mapping)
                elif vendor == '浜松ベジタブル':
                    products, price_errors = extract_hamamatsu_products(df, week, current_mapping)
                elif vendor == 'アグリ':
                    products, price_errors = extract_aguri_products(df, week, current_mapping)
                elif vendor == 'おやさい':
                    products, price_errors = extract_oyasai_products(df, week, current_mapping)
                
                # Check for duplicates (品名, 取引先, 産地)
                seen_combinations = {}
                duplicates = []
                unique_products = []
                
                for product in products:
                    combination_key = (product['品名'], product['取引先'], product['産地'])
                    
                    if combination_key in seen_combinations:
                        # This is a duplicate - record it and skip
                        duplicates.append({
                            '品名': product['品名'],
                            '取引先': product['取引先'],
                            '産地': product['産地'],
                            'kg単価': product['kg単価'],
                            '統一品名（カタカナ）': product['統一品名（カタカナ）'],
                            '既存のkg単価': seen_combinations[combination_key]
                        })
                        continue  # Skip this duplicate
                    
                    # Record this combination and its price
                    seen_combinations[combination_key] = product['kg単価']
                    unique_products.append(product)
                
                # Display price errors if any
                if len(price_errors) > 0:
                    st.error(f"❌ **価格エラー: {len(price_errors)}件の行で価格に問題があります**")
                    error_df = pd.DataFrame(price_errors)
                    st.dataframe(error_df, use_container_width=True)
                    st.warning("⚠️ これらの行はデータから除外されました。価格を確認してください。")
                
                # Display duplicates if any
                if len(duplicates) > 0:
                    st.warning(f"⚠️ **重複組み合わせが除外されました: {len(duplicates)}件の重複が見つかりました**")
                    st.info("以下の（品名, 取引先, 産地）の組み合わせは重複のため、CSVファイルには含まれていません。\nこれらのレコードは手動で追加するか、異なる名前でファイルを再アップロードしてください。")
                    duplicates_df = pd.DataFrame(duplicates)
                    duplicates_df = duplicates_df[['品名', '取引先', '産地', '統一品名（カタカナ）', 'kg単価', '既存のkg単価']]
                    duplicates_df.columns = ['品名', '取引先', '産地', '統一品名（カタカナ）', 'このレコードのkg単価', '既に含まれているレコードのkg単価']
                    st.dataframe(duplicates_df, use_container_width=True)
                
                if len(unique_products) == 0:
                    st.error("❌ データが抽出されませんでした。")
                else:
                    df_consolidated = pd.DataFrame(unique_products)
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
                    if len(duplicates) > 0:
                        st.info(f"ℹ️ 元のデータ: {len(products)}件 → 重複除外後: {len(df_consolidated)}件（{len(duplicates)}件の重複を除外）")
                    
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

