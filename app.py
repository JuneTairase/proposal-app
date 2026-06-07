import streamlit as st
st.set_page_config(layout="wide", page_title="埼玉県プロポーザル情報収集", page_icon="📋")

import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
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
    {'自治体': '上尾市',   'url': 'https://www.city.ageo.lg.jp/page/04111905241.html',                                 'base_url': 'https://www.city.ageo.lg.jp'},
    {'自治体': '久喜市',   'url': 'https://www.city.kuki.lg.jp/shisei/jigyo/nyusatsu_keiyaku/1002295/index.html',      'base_url': 'https://www.city.kuki.lg.jp'},
    {'自治体': '新座市',   'url': 'https://www.city.niiza.lg.jp/life/18/111/',                                          'base_url': 'https://www.city.niiza.lg.jp'},
    {'自治体': '八潮市',   'url': 'https://www.city.yashio.lg.jp/jigyosha/nyusatsu_keiyaku/hatchujoho/index.html',     'base_url': 'https://www.city.yashio.lg.jp'},
    {'自治体': '三郷市',   'url': 'https://www.city.misato.lg.jp/soshiki/somu/keiyaku/nyusatsujouhou/index.html',      'base_url': 'https://www.city.misato.lg.jp'},
    {'自治体': '狭山市',   'url': 'https://www.city.sayama.saitama.jp/jigyo/index.html',                               'base_url': 'https://www.city.sayama.saitama.jp'},
    {'自治体': '入間市',   'url': 'https://www.city.iruma.saitama.jp/shigoto_sangyo/nyusatsu_keiyaku/proposal/index.html', 'base_url': 'https://www.city.iruma.saitama.jp'},
    {'自治体': '深谷市',   'url': 'https://www.city.fukaya.saitama.jp/business/nyusatsukeiyaku/hachu/index.html',      'base_url': 'https://www.city.fukaya.saitama.jp'},
    {'自治体': '行田市',   'url': 'https://www.city.gyoda.lg.jp/shigoto_sangyo/nyusatsu_keiyaku/index.html',           'base_url': 'https://www.city.gyoda.lg.jp'},
    {'自治体': '羽生市',   'url': 'https://www.city.hanyu.lg.jp/categories/bunya/jigyosha/nyusatsu/',                  'base_url': 'https://www.city.hanyu.lg.jp'},
    {'自治体': '東松山市', 'url': 'https://www.city.higashimatsuyama.lg.jp/life/2/24/',                                 'base_url': 'https://www.city.higashimatsuyama.lg.jp'},
    {'自治体': '飯能市',   'url': 'https://www.city.hanno.lg.jp/sangyo_jigyoshamuke/nyusatsu_keiyaku_saikenshatoroku/nyusatsujoho/index.html', 'base_url': 'https://www.city.hanno.lg.jp'},
    {'自治体': '朝霞市',   'url': 'https://www.city.asaka.lg.jp/life/2/54/',                                           'base_url': 'https://www.city.asaka.lg.jp'},
    {'自治体': '戸田市',   'url': 'https://www.city.toda.saitama.jp/life/6/50/',                                        'base_url': 'https://www.city.toda.saitama.jp'},
    {'自治体': '鴻巣市',   'url': 'https://www.city.kounosu.saitama.jp/site/nyusatsukeiyaku/3456.html',                'base_url': 'https://www.city.kounosu.saitama.jp'},
    {'自治体': '加須市',   'url': 'https://www.city.kazo.lg.jp/shigoto_sangyo/nyusatsu_keiyaku/proposal/index.html',  'base_url': 'https://www.city.kazo.lg.jp'},
    {'自治体': '富士見市', 'url': 'https://www.city.fujimi.saitama.jp/60jigyo/17nyuusatsu/proposal/',                  'base_url': 'https://www.city.fujimi.saitama.jp'},
]

SCRAPE_KEYWORDS = ['プロポーザル', '企画提案競技', '企画提案募集', '企画提案']
CSV_PATH = 'proposal_data.csv'

# ───────────────────────────────────────────
# 年度計算
# ───────────────────────────────────────────
def get_reiwa_year():
    today = datetime.today()
    fiscal_year = today.year if today.month >= 4 else today.year - 1
    return fiscal_year - 2018

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
    results = []
    errors  = []
    total   = len(MUNICIPALITIES)
    status_area  = st.empty()
    progress_bar = st.progress(0)
    done_count   = [0]
    log_lines    = []

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
            status_area.markdown('\n\n'.join(log_lines[-6:]))

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
# セッション初期化
# ───────────────────────────────────────────
if 'exclude_kw_list' not in st.session_state:
    st.session_state['exclude_kw_list'] = list(DEFAULT_EXCLUDE)
for _kw in st.session_state['exclude_kw_list']:
    _key = f'exkw_{_kw}'
    if _key not in st.session_state:
        st.session_state[_key] = True

# ───────────────────────────────────────────
# UI：ヘッダー
# ───────────────────────────────────────────
st.title('📋 埼玉県プロポーザル情報収集')
st.caption('埼玉県各市町村のプロポーザル情報を並列取得します')
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

df = load_data(CSV_PATH)

if df.empty:
    st.warning('データがありません。「最新情報を取得」ボタンを押してください。')
    st.stop()

with col_info:
    latest_date = df['取得日'].max()
    st.info(f'最終取得日：{latest_date}')

st.divider()

# ───────────────────────────────────────────
# サイドバー
# ───────────────────────────────────────────
st.sidebar.header('🔍 絞り込み条件')

# ── 自治体選択 ──
st.sidebar.subheader('① 自治体')
municipalities_list = [m['自治体'] for m in MUNICIPALITIES]

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

# 除外キーワード適用
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

# ───────────────────────────────────────────
# 結果表示
# ───────────────────────────────────────────
st.subheader(f'検索結果：{len(filtered_df)} 件')

# 自治体別件数サマリー
all_municipalities = [m['自治体'] for m in MUNICIPALITIES]
cols_m = st.columns(4)
for i, name in enumerate(all_municipalities):
    count = int(filtered_df[filtered_df['自治体'] == name].shape[0]) if not filtered_df.empty else 0
    cols_m[i % 4].metric(name, f'{count}件')

if filtered_df.empty:
    st.info('条件に合う情報がありません。')

st.divider()

# 一覧表示
for _, row in filtered_df.iterrows():
    label = f"【{row['自治体']}】{row['タイトル']}"
    with st.expander(label):
        st.markdown(f"🔗 [詳細ページを開く]({row['URL']})")
        st.caption(f"取得日：{row['取得日']}")

# ───────────────────────────────────────────
# 注釈・懸念事項
# ───────────────────────────────────────────
st.divider()
st.subheader('📝 注釈・懸念事項')
st.markdown('''
**【スクレイピングキーワードについて】**
現在のスクレイピングキーワードは「プロポーザル」「企画提案競技」「企画提案募集」「企画提案」の4つです。
「企画提案」を追加したことで情報の取りこぼしは減りましたが、関係のない案件が混入する可能性があります。
ノイズが気になる場合はサイドバーの「除外キーワード管理」で調整してください。

**【0件または件数が少ない可能性がある自治体】**
以下の自治体はプロポーザル専用の一覧ページがなく、各部署に情報が分散しているため、
取得できていない案件がある可能性があります。

| 自治体 | 懸念内容 |
|---|---|
| 上尾市 | 専用ページなし。各部署に分散しているため取りこぼしの可能性あり |
| 三郷市 | 専用ページなし。各部署に分散しているため取りこぼしの可能性あり |
| 狭山市 | 専用ページなし。各部署に分散しているため取りこぼしの可能性あり |
| 羽生市 | 専用ページなし。各部署に分散しているため取りこぼしの可能性あり |
| 戸田市 | 専用ページなし。入札情報トップから取得しているため取りこぼしの可能性あり |
| 鴻巣市 | プロポーザル選定結果ページのみ参照。募集中案件が取れていない可能性あり |
| 行田市 | 専用ページはあるが掲載件数が少ない。各部署に分散している可能性あり |
| 飯能市 | 入札情報全般ページを参照。プロポーザル以外の情報も混入する可能性あり |
''')
