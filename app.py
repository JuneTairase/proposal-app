import streamlit as st
st.set_page_config(layout="wide", page_title="埼玉県プロポーザル情報収集")
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os

# 自治体設定
MUNICIPALITIES = [
    {
        '自治体': '埼玉県',
        'url': 'https://www.pref.saitama.lg.jp/a0212/kense/tetsuzuki/nyusatsu/buppin/index.html',
        'base_url': 'https://www.pref.saitama.lg.jp',
    },
    {
        '自治体': 'さいたま市',
        'url': 'https://www.city.saitama.lg.jp/005/001/017/012/index.html',
        'base_url': 'https://www.city.saitama.lg.jp',
    },
    {
        '自治体': '川口市',
        'url': 'https://www.city.kawaguchi.lg.jp/jigyoshamuke/nyusatsu_keiyakujoho/puropokikaku/index.html',
        'base_url': 'https://www.city.kawaguchi.lg.jp',
    },
    {
        '自治体': '川越市',
        'url': 'https://www.city.kawagoe.saitama.jp/sangyo/nyusatsu/1011749/1011776/1017300/index.html',
        'base_url': 'https://www.city.kawagoe.saitama.jp',
    },
    {
        '自治体': '越谷市',
        'url': 'https://www.city.koshigaya.saitama.jp/kurashi_shisei/jigyosha/nyusatukeiyaku/proposal/index.html',
        'base_url': 'https://www.city.koshigaya.saitama.jp',
    },
    {
        '自治体': '所沢市',
        'url': 'https://www.city.tokorozawa.saitama.jp/shiseijoho/jigyo/news/index.html',
        'base_url': 'https://www.city.tokorozawa.saitama.jp',
    },
    {
        '自治体': '熊谷市',
        'url': 'https://www.city.kumagaya.lg.jp/category/boshu/index.html',
        'base_url': 'https://www.city.kumagaya.lg.jp',
    },
    {
        '自治体': '春日部市',
        'url': 'https://www.city.kasukabe.lg.jp/jigyoshamuke/nyusatsu_keiyaku/nyusatsukokokuichiran/index.html',
        'base_url': 'https://www.city.kasukabe.lg.jp',
    },
    {
        '自治体': '草加市',
        'url': 'https://www.city.soka.saitama.jp/li/050/070/030/050/index.html',
        'base_url': 'https://www.city.soka.saitama.jp',
    },
    {
        '自治体': '上尾市',
        'url': 'https://www.city.ageo.lg.jp/life/3/19/',
        'base_url': 'https://www.city.ageo.lg.jp',
    },
    {
        '自治体': '久喜市',
        'url': 'https://www.city.kuki.lg.jp/shisei/jigyo/nyusatsu_keiyaku/1002295/index.html',
        'base_url': 'https://www.city.kuki.lg.jp',
    },
    {
        '自治体': '新座市',
        'url': 'https://www.city.niiza.lg.jp/life/18/111/',
        'base_url': 'https://www.city.niiza.lg.jp',
    },
        {
        '自治体': '八潮市',
        'url': 'https://www.city.yashio.lg.jp/jigyosha/nyusatsu_keiyaku/hatchujoho/index.html',
        'base_url': 'https://www.city.yashio.lg.jp',
    },
    {
        '自治体': '三郷市',
        'url': 'https://www.city.misato.lg.jp/soshiki/somu/keiyaku/kohyo_shiryo/index.html',
        'base_url': 'https://www.city.misato.lg.jp',
    },
    {
        '自治体': '狭山市',
        'url': 'https://www.city.sayama.saitama.jp/jigyo/koubo/index.html',
        'base_url': 'https://www.city.sayama.saitama.jp',
    },
    {
        '自治体': '入間市',
        'url': 'https://www.city.iruma.saitama.jp/shigoto_sangyo/nyusatsu_keiyaku/proposal/index.html',
        'base_url': 'https://www.city.iruma.saitama.jp',
    },  
]

KEYWORDS = ['プロポーザル', '企画提案競技', '企画提案募集']
CSV_PATH = 'proposal_data.csv'

# スクレイピング関数
def scrape_all():
    results = []
    status = st.empty()
    progress = st.progress(0)

    for i, m in enumerate(MUNICIPALITIES):
        status.write(f'⏳ {m["自治体"]} を取得中...')
        try:
            response = requests.get(m['url'], timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            main_content = soup.find('div', {'id': 'tmp_main'}) or soup
            links = main_content.find_all('a')

            for link in links:
                text = link.get_text(strip=True)
                href = link.get('href', '')
                if any(kw in text for kw in KEYWORDS):
                    full_url = m['base_url'] + href if href.startswith('/') else href
                    results.append({
                        '自治体': m['自治体'],
                        'タイトル': text,
                        'URL': full_url,
                        '取得日': datetime.today().strftime('%Y-%m-%d')
                    })
            status.write(f'✅ {m["自治体"]} 完了')
            time.sleep(1)
        except Exception as e:
            status.write(f'❌ {m["自治体"]} エラー：{e}')

        progress.progress((i + 1) / len(MUNICIPALITIES))

    df = pd.DataFrame(results).drop_duplicates(subset=['タイトル', '自治体'])
    df.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')
    status.write(f'✅ 全自治体の取得完了！合計 {len(df)} 件')
    return df

# データ読み込み
def load_data():
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH)
    return pd.DataFrame(columns=['自治体', 'タイトル', 'URL', '取得日'])

# ヘッダー
st.title('埼玉県プロポーザル情報収集')
st.caption('埼玉県各市町村のプロポーザル情報を収集・表示します')
st.divider()

# 最新情報取得ボタン
col1, col2 = st.columns([1, 3])
with col1:
    if st.button('🔄 最新情報を取得', use_container_width=True):
        with st.spinner('取得中...'):
            df = scrape_all()
        st.success('取得完了！')
        st.rerun()

# データ読み込み
df = load_data()

if df.empty:
    st.warning('データがありません。「最新情報を取得」ボタンを押してください。')
    st.stop()

# 取得日表示
with col2:
    if '取得日' in df.columns and not df.empty:
        latest_date = df['取得日'].max()
        st.info(f'最終取得日：{latest_date}')

st.divider()

# サイドバー：絞り込み条件
st.sidebar.header('🔍 絞り込み条件')
st.sidebar.subheader('自治体を選択')

municipalities_list = df['自治体'].unique().tolist()

# session_stateの初期化
for m in municipalities_list:
    if f'cb_{m}' not in st.session_state:
        st.session_state[f'cb_{m}'] = True

# 全選択・全解除ボタン
col_a, col_b = st.sidebar.columns(2)
if col_a.button('全選択', use_container_width=True):
    for m in municipalities_list:
        st.session_state[f'cb_{m}'] = True
if col_b.button('全解除', use_container_width=True):
    for m in municipalities_list:
        st.session_state[f'cb_{m}'] = False

# チェックボックス（2列表示）
selected = []
cols = st.sidebar.columns(2)
for i, m in enumerate(municipalities_list):
    key = f'cb_{m}'
    if key not in st.session_state:
        st.session_state[key] = True
    val = cols[i % 2].checkbox(m, value=st.session_state[key], key=key)
    if val:
        selected.append(m)

st.sidebar.divider()

# キーワード入力＋検索ボタン
st.sidebar.subheader('キーワードで絞り込み')
keyword = st.sidebar.text_input('キーワードを入力', placeholder='例：IT、福祉、調査')
search_button = st.sidebar.button('🔍 検索する', use_container_width=True)

# 現在の年度を自動計算（4月以降が新年度）
today = datetime.today()
if today.month >= 4:
    current_year = today.year
else:
    current_year = today.year - 1

# 現在の元号年を計算（令和は2019年が元年）
reiwa_year = current_year - 2018
current_reiwa = f'令和{reiwa_year}年度'
prev_reiwa = f'令和{reiwa_year - 1}年度'

# 除外キーワード（募集終了済み＋古い年度を自動除外）
exclude_keywords = [
    '募集終了', '終了しました', '決定しました', '選定結果',
    '審査結果', '結果について', '候補者の決定', '平成'
]

# 令和1年度〜前年度を自動で除外リストに追加
for y in range(1, reiwa_year):
    exclude_keywords.append(f'令和{y}年度')

# 絞り込み処理
filtered_df = df[df['自治体'].isin(selected)]

# 除外キーワード
filtered_df = filtered_df[
    ~filtered_df['タイトル'].apply(
        lambda x: any(kw in str(x) for kw in exclude_keywords)
    )
]

# キーワード絞り込み（ボタンを押したときだけ）
if search_button and keyword:
    filtered_df = filtered_df[filtered_df['タイトル'].str.contains(keyword, na=False)]
elif not search_button and keyword == '':
    pass  # キーワードなしはそのまま表示
# 結果表示
st.subheader(f'検索結果：{len(filtered_df)}件')

if not filtered_df.empty and '自治体' in filtered_df.columns:
    col1, col2, col3 = st.columns(3)
    municipalities_count = filtered_df['自治体'].value_counts()
    for i, (name, count) in enumerate(municipalities_count.items()):
        if i % 3 == 0:
            col1.metric(name, f'{count}件')
        elif i % 3 == 1:
            col2.metric(name, f'{count}件')
        else:
            col3.metric(name, f'{count}件')
elif filtered_df.empty:
    st.info('条件に合う情報がありません。自治体を選択するか、キーワードを変更してください。')

# 一覧表示
for _, row in filtered_df.iterrows():
    with st.expander(f"【{row['自治体']}】{row['タイトル']}"):
        st.write(f" [詳細ページを開く]({row['URL']})")
        st.write(f" 取得日：{row['取得日']}")