import streamlit as st
st.set_page_config(layout="wide", page_title="埼玉県プロポーザル情報収集", page_icon="📋")

import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# ───────────────────────────────────────────
# 自治体設定
# ───────────────────────────────────────────
MUNICIPALITIES = [
    {'自治体': '埼玉県',   'url': 'https://www.pref.saitama.lg.jp/a0212/kense/tetsuzuki/nyusatsu/buppin/index.html', 'base_url': 'https://www.pref.saitama.lg.jp'},
    {'自治体': 'さいたま市', 'url': 'https://www.city.saitama.lg.jp/005/001/017/012/index.html',                      'base_url': 'https://www.city.saitama.lg.jp'},
    {'自治体': '川口市',   'url': 'https://www.city.kawaguchi.lg.jp/jigyoshamuke/nyusatsu_keiyakujoho/puropokikaku/index.html', 'base_url': 'https://www.city.kawaguchi.lg.jp'},
    {'自治体': '川越市',   'url': 'https://www.city.kawagoe.saitama.jp/sangyo/nyusatsu/1011749/1011776/1017300/index.html',     'base_url': 'https://www.city.kawagoe.saitama.jp'},
    {'自治体': '越谷市',   'url': 'https://www.city.koshigaya.saitama.jp/kurashi_shisei/jigyosha/nyusatukeiyaku/proposal/index.html', 'base_url': 'https://www.city.koshigaya.saitama.jp'},
    {'自治体': '所沢市',   'url': 'https://www.city.tokorozawa.saitama.jp/shiseijoho/jigyo/news/index.html',           'base_url': 'https://www.city.tokorozawa.saitama.jp'},
    {'自治体': '熊谷市',   'url': 'https://www.city.kumagaya.lg.jp/category/boshu/index.html',                         'base_url': 'https://www.city.kumagaya.lg.jp'},
    {'自治体': '春日部市', 'url': 'https://www.city.kasukabe.lg.jp/jigyoshamuke/nyusatsu_keiyaku/nyusatsukokokuichiran/index.html', 'base_url': 'https://www.city.kasukabe.lg.jp'},
    {'自治体': '草加市',   'url': 'https://www.city.soka.saitama.jp/li/050/070/030/050/index.html',                    'base_url': 'https://www.city.soka.saitama.jp'},
    {'自治体': '上尾市',   'url': 'https://www.city.ageo.lg.jp/life/3/19/',                                            'base_url': 'https://www.city.ageo.lg.jp'},
    {'自治体': '久喜市',   'url': 'https://www.city.kuki.lg.jp/shisei/jigyo/nyusatsu_keiyaku/1002295/index.html',      'base_url': 'https://www.city.kuki.lg.jp'},
    {'自治体': '新座市',   'url': 'https://www.city.niiza.lg.jp/life/18/111/',                                          'base_url': 'https://www.city.niiza.lg.jp'},
    {'自治体': '八潮市',   'url': 'https://www.city.yashio.lg.jp/jigyosha/nyusatsu_keiyaku/hatchujoho/index.html',     'base_url': 'https://www.city.yashio.lg.jp'},
    {'自治体': '三郷市',   'url': 'https://www.city.misato.lg.jp/soshiki/somu/keiyaku/kohyo_shiryo/index.html',         'base_url': 'https://www.city.misato.lg.jp'},
    {'自治体': '狭山市',   'url': 'https://www.city.sayama.saitama.jp/jigyo/koubo/index.html',                         'base_url': 'https://www.city.sayama.saitama.jp'},
    {'自治体': '入間市',   'url': 'https://www.city.iruma.saitama.jp/shigoto_sangyo/nyusatsu_keiyaku/proposal/index.html', 'base_url': 'https://www.city.iruma.saitama.jp'},
    {'自治体': '深谷市',   'url': 'https://www.city.fukaya.saitama.jp/business/nyusatsukeiyaku/hachu/index.html',               'base_url': 'https://www.city.fukaya.saitama.jp'},
    {'自治体': '行田市',   'url': 'https://www.city.gyoda.lg.jp/shigoto_sangyo/nyusatsu_keiyaku/index.html',                    'base_url': 'https://www.city.gyoda.lg.jp'},
    {'自治体': '羽生市',   'url': 'https://www.city.hanyu.lg.jp/categories/kubun/boshu/',                                       'base_url': 'https://www.city.hanyu.lg.jp'},
    {'自治体': '東松山市', 'url': 'https://www.city.higashimatsuyama.lg.jp/life/2/24/',                                         'base_url': 'https://www.city.higashimatsuyama.lg.jp'},
    {'自治体': '飯能市',   'url': 'https://www.city.hanno.lg.jp/sangyo_jigyoshamuke/nyusatsu_keiyaku_saikenshatoroku/nyusatsujoho/index.html', 'base_url': 'https://www.city.hanno.lg.jp'},
]

SCRAPE_KEYWORDS = ['プロポーザル', '企画提案競技', '企画提案募集']
CSV_PATH      = 'proposal_data.csv'
CSV_PREV_PATH = 'proposal_data_prev.csv'

# ───────────────────────────────────────────
# 年度計算
# ───────────────────────────────────────────
def get_reiwa_year():
    today = datetime.today()
    fiscal_year = today.year if today.month >= 4 else today.year - 1
    return fiscal_year - 2018  # 令和年

REIWA_YEAR = get_reiwa_year()

# ───────────────────────────────────────────
# デフォルト除外キーワード
# ───────────────────────────────────────────
DEFAULT_EXCLUDE = [
    '募集終了', '終了しました', '決定しました', '選定結果',
    '審査結果', '結果について', '候補者の決定', '平成',
] + [f'令和{y}年度' for y in range(1, REIWA_YEAR)]

# ───────────────────────────────────────────
# 1自治体スクレイピング（並列用）
# ───────────────────────────────────────────
def scrape_one(m):
    rows = []
    error = None
    try:
        resp = requests.get(m['url'], timeout=12, headers={'User-Agent': 'Mozilla/5.0'})
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        main = soup.find('div', {'id': 'tmp_main'}) or soup
        for link in main.find_all('a'):
            text = link.get_text(strip=True)
            href = link.get('href', '')
            if any(kw in text for kw in SCRAPE_KEYWORDS):
                full_url = (m['base_url'] + href) if href.startswith('/') else href
                rows.append({
                    '自治体':  m['自治体'],
                    'タイトル': text,
                    'URL':    full_url,
                    '取得日':  datetime.today().strftime('%Y-%m-%d'),
                })
    except Exception as e:
        error = str(e)
    return m['自治体'], rows, error

# ───────────────────────────────────────────
# 並列スクレイピング
# ───────────────────────────────────────────
def scrape_all():
    # 前回データを退避
    if os.path.exists(CSV_PATH):
        import shutil
        shutil.copy(CSV_PATH, CSV_PREV_PATH)

    results = []
    errors  = []
    total   = len(MUNICIPALITIES)

    status_area  = st.empty()
    progress_bar = st.progress(0)
    done_count   = [0]

    log_lines = []

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(scrape_one, m): m for m in MUNICIPALITIES}
        for future in as_completed(futures):
            name, rows, err = future.result()
            done_count[0] += 1
            progress_bar.progress(done_count[0] / total)
            if err:
                log_lines.append(f'❌ {name}：{err}')
                errors.append(name)
            else:
                log_lines.append(f'✅ {name}：{len(rows)}件')
                results.extend(rows)
            status_area.markdown('\n\n'.join(log_lines[-6:]))  # 直近6行表示

    df = pd.DataFrame(results).drop_duplicates(subset=['URL', '自治体'])
    df.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')

    status_area.empty()
    progress_bar.empty()
    return df, errors

# ───────────────────────────────────────────
# データ読み込み
# ───────────────────────────────────────────
def load_data(path=CSV_PATH):
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=['自治体', 'タイトル', 'URL', '取得日'])

# ───────────────────────────────────────────
# 新着判定
# ───────────────────────────────────────────
def mark_new(df, prev_df):
    if prev_df.empty:
        df['新着'] = True
        return df
    prev_urls = set(prev_df['URL'].dropna())
    df['新着'] = ~df['URL'].isin(prev_urls)
    return df

# ───────────────────────────────────────────
# セッション初期化
# ───────────────────────────────────────────
# 除外キーワード：リストのみ管理。ON/OFFはst.session_stateのキー 'exkw_XXX' で完全管理
if 'exclude_kw_list' not in st.session_state:
    st.session_state['exclude_kw_list'] = list(DEFAULT_EXCLUDE)
# 各キーワードのチェック状態を初期化（まだキーがないものだけ）
for _kw in st.session_state['exclude_kw_list']:
    _key = f'exkw_{_kw}'
    if _key not in st.session_state:
        st.session_state[_key] = True

# ───────────────────────────────────────────
# UI：ヘッダー
# ───────────────────────────────────────────
st.title('📋 埼玉県プロポーザル情報収集')
st.caption('埼玉県各市町村のプロポーザル情報を並列取得・差分表示します')
st.divider()

col_btn, col_info = st.columns([1, 3])
with col_btn:
    if st.button('🔄 最新情報を取得', use_container_width=True):
        with st.spinner('並列取得中...'):
            df_new, errs = scrape_all()
        if errs:
            st.warning(f'一部エラー：{", ".join(errs)}')
        else:
            st.success(f'取得完了！{len(df_new)} 件')
        st.rerun()

df      = load_data(CSV_PATH)
prev_df = load_data(CSV_PREV_PATH)

if df.empty:
    st.warning('データがありません。「最新情報を取得」ボタンを押してください。')
    st.stop()

df = mark_new(df, prev_df)

with col_info:
    latest_date = df['取得日'].max()
    new_count_total = int(df['新着'].sum())
    info_placeholder = st.empty()  # フィルター後に更新するため placeholder を使う

st.divider()

# ───────────────────────────────────────────
# サイドバー
# ───────────────────────────────────────────
st.sidebar.header('🔍 絞り込み条件')

# ── 自治体選択 ──
st.sidebar.subheader('① 自治体')
municipalities_list = df['自治体'].unique().tolist()

for m in municipalities_list:
    if f'cb_{m}' not in st.session_state:
        st.session_state[f'cb_{m}'] = True

col_a, col_b = st.sidebar.columns(2)
if col_a.button('全選択', use_container_width=True):
    for m in municipalities_list:
        st.session_state[f'cb_{m}'] = True
    st.rerun()
if col_b.button('全解除', use_container_width=True):
    for m in municipalities_list:
        st.session_state[f'cb_{m}'] = False
    st.rerun()

selected = []
cols2 = st.sidebar.columns(2)
for i, m in enumerate(municipalities_list):
    key = f'cb_{m}'
    val = cols2[i % 2].checkbox(m, value=st.session_state[key], key=key)
    if val:
        selected.append(m)

st.sidebar.divider()

# ── キーワード絞り込み ──
st.sidebar.subheader('② キーワード絞り込み')
keyword = st.sidebar.text_input('キーワード（リアルタイム反映）', placeholder='例：IT、福祉、調査')
new_only = st.sidebar.checkbox('🆕 新着のみ表示', value=False)

st.sidebar.divider()

# ── 除外キーワード管理 ──
st.sidebar.subheader('③ 除外キーワード管理')
with st.sidebar.expander('除外キーワードを編集', expanded=False):
    st.caption('チェックを外すと除外しません（キーワード自体は消えません）')
    for kw in st.session_state['exclude_kw_list']:
        _key = f'exkw_{kw}'
        if _key not in st.session_state:
            st.session_state[_key] = True
        st.checkbox(kw, key=_key)

    st.markdown('---')
    new_ex = st.text_input('除外キーワードを追加', key='new_exclude_input')
    if st.button('追加', key='add_exclude'):
        if new_ex and new_ex not in st.session_state['exclude_kw_list']:
            st.session_state['exclude_kw_list'].append(new_ex)
            st.session_state[f'exkw_{new_ex}'] = True
            st.rerun()

st.sidebar.divider()

# ── CSV出力 ──
st.sidebar.subheader('④ データ出力')
csv_bytes = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
st.sidebar.download_button(
    label='📥 全データをCSVダウンロード',
    data=csv_bytes,
    file_name=f'proposal_{datetime.today().strftime("%Y%m%d")}.csv',
    mime='text/csv',
    use_container_width=True,
)

# ───────────────────────────────────────────
# 絞り込み処理
# ───────────────────────────────────────────
filtered_df = df[df['自治体'].isin(selected)].copy()

# 除外キーワード適用（session_stateのキーがTrueのもののみ）
ex_kws = [
    kw for kw in st.session_state.get('exclude_kw_list', [])
    if st.session_state.get(f'exkw_{kw}', True)
]
if ex_kws:
    filtered_df = filtered_df[
        ~filtered_df['タイトル'].apply(lambda x: any(kw in str(x) for kw in ex_kws))
    ]

# キーワード絞り込み（リアルタイム）
if keyword:
    filtered_df = filtered_df[filtered_df['タイトル'].str.contains(keyword, na=False)]

# 新着のみ
if new_only:
    filtered_df = filtered_df[filtered_df['新着'] == True]

# ───────────────────────────────────────────
# 結果表示
# ───────────────────────────────────────────
new_in_filtered = int(filtered_df['新着'].sum()) if '新着' in filtered_df.columns else 0

# ヘッダーの新着件数をフィルター後の件数で更新
if new_count_total > 0:
    info_placeholder.info(
        f'最終取得日：{latest_date}　／　前回比 新着 {new_count_total} 件（表示対象 {new_in_filtered} 件）'
    )
else:
    info_placeholder.info(f'最終取得日：{latest_date}　／　前回比 新着なし')

st.subheader(f'検索結果：{len(filtered_df)} 件　（うち新着 {new_in_filtered} 件）')

# 自治体別件数サマリー
if not filtered_df.empty:
    mc = filtered_df['自治体'].value_counts()
    cols_m = st.columns(min(len(mc), 4))
    for i, (name, count) in enumerate(mc.items()):
        new_c = int(filtered_df[filtered_df['自治体'] == name]['新着'].sum())
        badge = f' 🆕{new_c}' if new_c > 0 else ''
        cols_m[i % 4].metric(name, f'{count}件{badge}')
else:
    st.info('条件に合う情報がありません。')

st.divider()

# 一覧表示
for _, row in filtered_df.iterrows():
    is_new  = row.get('新着', False)
    new_tag = '　🆕 新着' if is_new else ''
    label   = f"【{row['自治体']}】{row['タイトル']}{new_tag}"
    with st.expander(label, expanded=is_new):
        st.markdown(f"🔗 [詳細ページを開く]({row['URL']})")
        st.caption(f"取得日：{row['取得日']}")
        if is_new:
            st.success('✨ 前回取得時には存在しなかった新着情報です')
