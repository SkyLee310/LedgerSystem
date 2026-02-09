import streamlit as st
import pandas as pd
import plotly.express as px
import backend
from datetime import date

# === 1. 页面配置 (必须在最前面) ===
st.set_page_config(
    page_title="My Ledger Pro",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="auto"
)

CURRENCY = "RM"

# === 2. 核心 UI 样式优化 (CSS) ===
# 这里我们注入 CSS 来美化 Metric 卡片和调整间距
st.markdown("""
    <style>
    /* 1. 隐藏多余的菜单和页脚 */
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;}

    /* 2. 优化顶部留白 */
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    /* 3. Metric 卡片样式化 (修复版：适配深色模式) */
    div[data-testid="stMetric"] {
        background-color: #262730; /* 改成深灰色，适配深色模式 */
        border: 1px solid #464b5c; /* 边框颜色调深 */
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); /* 阴影加深一点 */
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.5);
        border-color: #808495;
    }

    /* 4. 让 Tab 标题更大更清晰 */
    button[data-baseweb="tab"] {
        font-size: 16px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# === 3. 语言包与辅助函数 ===
TRANS = {
    "app_title": {"CN": "我的账本", "EN": "My Ledger Pro"},
    "sidebar_title": {"CN": "📚 账本列表", "EN": "📚 Ledgers"},
    "current_ledger": {"CN": "当前账本", "EN": "Current Ledger"},

    # 概览卡片
    "total_income": {"CN": "总收入", "EN": "Total Income"},
    "total_expense": {"CN": "总支出", "EN": "Total Expense"},
    "balance": {"CN": "结余", "EN": "Net Balance"},

    # 记账区
    "header_entry": {"CN": "✨ 记一笔", "EN": "✨ New Transaction"},
    "date": {"CN": "日期", "EN": "Date"},
    "category": {"CN": "分类", "EN": "Category"},
    "amount": {"CN": "金额", "EN": "Amount"},
    "note": {"CN": "备注", "EN": "Note"},
    "btn_save": {"CN": "💾 立即保存", "EN": "💾 Save Record"},

    # 标签页
    "tab_overview": {"CN": "📊 概览", "EN": "📊 Dashboard"},
    "tab_stats": {"CN": "📉 分析", "EN": "📉 Analytics"},
    "tab_data": {"CN": "📋 明细", "EN": "📋 Records"},

    # 筛选
    "filter_label": {"CN": "🔍 筛选与搜索", "EN": "🔍 Filter & Search"},
    "filter_cat": {"CN": "按分类", "EN": "By Category"},
    "filter_type": {"CN": "按类型", "EN": "By Type"},
    "all": {"CN": "全部", "EN": "All"},

    # 设置
    "settings": {"CN": "⚙️ 设置", "EN": "⚙️ Settings"},
    "create_ledger": {"CN": "创建新账本", "EN": "Create Ledger"},
    "manage_cats": {"CN": "分类管理", "EN": "Categories"},

    # 提示
    "welcome": {"CN": "欢迎回来！", "EN": "Welcome Back!"},
    "empty": {"CN": "暂无数据，快去记一笔吧！", "EN": "No records yet. Add one now!"}
}

CAT_TRANS = {
    "餐饮": "🍔 Food", "交通": "🚗 Transport", "购物": "🛍️ Shopping",
    "居住": "🏠 Housing", "工资": "💰 Salary", "娱乐": "🎮 Fun",
    "医疗": "💊 Medical", "其他": "📦 Others"
}


def T(key):
    lang = st.session_state.get('language_code', 'EN')
    return TRANS.get(key, {}).get(lang, key)


def get_cat_display(cat_name):
    lang = st.session_state.get('language_code', 'CN')
    if lang == 'EN': return CAT_TRANS.get(cat_name, cat_name)
    return cat_name


# 统一配色方案 (UX 统一性)
COLOR_MAP = {
    "收入": "#00CC96", "Income": "#00CC96",  # 绿色
    "支出": "#EF553B", "Expense": "#EF553B"  # 红色
}


# === 4. 回调函数 ===
def save_callback():
    lang = st.session_state.get('language_code', 'CN')
    amt = st.session_state.get('input_amount', 0.0)
    cat = st.session_state.get(f'input_category_{lang}', "")
    typ = st.session_state.get('input_type', "")
    note = st.session_state.get('input_note', "")
    dt = st.session_state.get('input_date', date.today())
    active_id = st.session_state.get('active_ledger_id')

    if active_id and amt > 0 and cat:
        db_type = "Expense" if any(x in typ for x in ["支出", "Expense"]) else "Income"
        backend.save_record(active_id, dt, db_type, cat, amt, note)
        st.toast("✅ " + ("已保存!" if lang == 'CN' else "Saved Successfully!"))
    elif amt <= 0:
        st.error("Amount must be > 0")


def add_cat_callback():
    new_c = st.session_state.get('new_cat_input')
    active_id = st.session_state.get('active_ledger_id')
    if active_id and new_c and backend.add_category(active_id, new_c):
        st.toast(f"Tag added: {new_c}")
        st.session_state['new_cat_input'] = ""


def del_cat_callback():
    del_c = st.session_state.get('del_cat_select')
    active_id = st.session_state.get('active_ledger_id')
    if active_id and del_c:
        backend.delete_category(active_id, del_c)
        st.toast(f"Tag removed: {del_c}")


# === 5. 程序入口 ===
backend.init_db()
all_ledgers = backend.get_ledgers()
ledger_names = [L[1] for L in all_ledgers]
ledger_map = {L[1]: L[0] for L in all_ledgers}

# --- Sidebar ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2920/2920349.png", width=50)  # Logo 占位
    st.markdown("### " + T("sidebar_title"))

    # 语言切换 (使用 segmented control 更好看，但需要较新版 streamlit，这里用 radio horizontal)
    st.radio("Language", ["CN", "EN"], horizontal=True, label_visibility="collapsed", key="language_code")

    if ledger_names:
        selected_ledger_name = st.selectbox(T("current_ledger"), ledger_names)
        current_ledger_id = ledger_map[selected_ledger_name]
        st.session_state['active_ledger_id'] = current_ledger_id
    else:
        st.warning("⚠️ No Ledgers")
        current_ledger_id = None
        selected_ledger_name = None

    st.divider()

    # 折叠式设置菜单 (保持侧边栏整洁)
    with st.expander(T("settings")):
        # 1. 新建账本
        st.caption(T("create_ledger"))
        new_ledger_name = st.text_input("Name", key="new_ledger_input", label_visibility="collapsed",
                                        placeholder="New Ledger Name")
        if st.button("➕ " + T("create_ledger"), use_container_width=True):
            if new_ledger_name and new_ledger_name not in ledger_names:
                backend.add_ledger(new_ledger_name)
                st.rerun()

        st.divider()

        # 2. 删除账本
        if ledger_names:
            ledger_to_del = st.selectbox("Delete Ledger", ledger_names, key="del_ledger_select")
            if st.button("🗑️ Delete", type="primary", use_container_width=True):
                backend.delete_ledger(ledger_map[ledger_to_del])
                st.rerun()

    if selected_ledger_name:
        with st.expander(T("manage_cats")):
            current_categories = backend.get_categories(current_ledger_id)
            c1, c2 = st.tabs(["➕ Add", "➖ Del"])
            with c1:
                st.text_input("New Cat", key='new_cat_input', label_visibility="collapsed", placeholder="Name...")
                st.button("Add", on_click=add_cat_callback, use_container_width=True)
            with c2:
                st.selectbox("Del Cat", current_categories, key='del_cat_select', label_visibility="collapsed")
                st.button("Remove", on_click=del_cat_callback, type="primary", use_container_width=True)

# --- Main Content ---

# 标题栏
if selected_ledger_name:
    st.title(f"{selected_ledger_name}")
    st.caption(f"{date.today().strftime('%Y-%m-%d')} | {T('welcome')}")
else:
    st.title(T("app_title"))
    st.stop()

# 记账输入区 (放在顶部 Expander，默认展开)
with st.expander(T("header_entry"), expanded=True):
    c1, c2, c3, c4 = st.columns([1.2, 1, 1.2, 1])  # 调整列宽比例

    with c1:
        st.date_input(T("date"), date.today(), key='input_date')
    with c2:
        type_opts = ["支出", "收入"] if st.session_state.get('language_code') == 'CN' else ["Expense", "Income"]
        st.selectbox(T("category"), type_opts, key='input_type', label_visibility="visible")
    with c3:
        current_cats = backend.get_categories(current_ledger_id)
        # 为分类添加默认 Emoji 前缀如果它没有的话 (纯 UI 优化)
        st.selectbox(T("category"), current_cats, format_func=get_cat_display,
                     key=f'input_category_{st.session_state.get("language_code")}')
    with c4:
        st.number_input(T("amount"), min_value=0.0, step=1.0, format="%.2f", key='input_amount')

    st.text_input(T("note"), key='input_note', placeholder="e.g. Lunch with friends...")

    # 保存按钮全宽
    st.button(T("btn_save"), on_click=save_callback, type="primary", use_container_width=True)

# 数据加载
raw_df = backend.get_all_records(current_ledger_id)

# 主要 Tabs
tab_overview, tab_stats, tab_data = st.tabs([T("tab_overview"), T("tab_stats"), T("tab_data")])

if raw_df.empty:
    st.info(T("empty"))
    st.stop()

# === Tab 1: 概览 (Cards + Simple Charts) ===
with tab_overview:
    # 1. 计算核心指标
    inc = raw_df[raw_df['type'].isin(['收入', 'Income'])]['amount'].sum()
    exp = raw_df[raw_df['type'].isin(['支出', 'Expense'])]['amount'].sum()
    bal = inc - exp

    # 2. 显示漂亮的指标卡片
    col1, col2, col3 = st.columns(3)
    col1.metric(T("total_income"), f"{CURRENCY} {inc:,.2f}", delta="Income")
    col2.metric(T("total_expense"), f"{CURRENCY} {exp:,.2f}", delta="-Expense", delta_color="inverse")
    col3.metric(T("balance"), f"{CURRENCY} {bal:,.2f}", delta="Net Worth", delta_color="off")

    st.divider()

    # 3. 概览图表 (左右布局)
    c_chart1, c_chart2 = st.columns(2)

    with c_chart1:
        st.subheader("📊 " + ("收支构成" if st.session_state.get('language_code') == 'CN' else "Composition"))
        # 环形图优化：去掉背景，增加空心
        chart_data = raw_df.groupby('category')['amount'].sum().reset_index()
        fig_pie = px.pie(chart_data, values='amount', names='category', hole=0.5)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    with c_chart2:
        st.subheader("📅 " + ("近期趋势" if st.session_state.get('language_code') == 'CN' else "Recent Trend"))
        # 简单的折线图
        daily_trend = raw_df.groupby('date')['amount'].sum().reset_index()
        fig_line = px.area(daily_trend, x='date', y='amount', color_discrete_sequence=['#636EFA'])
        fig_line.update_layout(margin=dict(t=0, b=0, l=0, r=0), yaxis_title=None, xaxis_title=None)
        st.plotly_chart(fig_line, use_container_width=True)

# === Tab 2: 深度分析 (Stacked Bar + Ranking) ===
with tab_stats:
    # 语言处理
    df_viz = raw_df.copy()
    if st.session_state.get('language_code') == 'EN':
        df_viz['type'] = df_viz['type'].replace({'收入': 'Income', '支出': 'Expense'})
        df_viz['category'] = df_viz['category'].map(CAT_TRANS).fillna(df_viz['category'])

    df_viz['month'] = pd.to_datetime(df_viz['date']).dt.to_period('M').astype(str)
    monthly_stats = df_viz.groupby(['month', 'type'])['amount'].sum().reset_index()

    # 柱状图优化：自定义颜色
    fig_bar = px.bar(
        monthly_stats, x='month', y='amount', color='type',
        barmode='group', text_auto='.2s',
        color_discrete_map=COLOR_MAP,
        title="Monthly Income vs Expense"
    )
    fig_bar.update_layout(xaxis_title="", yaxis_title="")
    st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # 排行榜
    exp_only = df_viz[df_viz['type'].isin(['支出', 'Expense'])]
    if not exp_only.empty:
        cat_rank = exp_only.groupby('category')['amount'].sum().reset_index().sort_values('amount', ascending=True)
        fig_rank = px.bar(
            cat_rank, y='category', x='amount', orientation='h',
            text_auto='.2s', title="Where did money go?",
            color='amount', color_continuous_scale='Reds'
        )
        fig_rank.update_layout(xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_rank, use_container_width=True)

# === Tab 3: 明细与筛选 (Smart Table) ===
with tab_data:
    with st.expander(T("filter_label"), expanded=False):
        f1, f2 = st.columns(2)
        sel_cats = f1.multiselect(T("filter_cat"), backend.get_categories(current_ledger_id),
                                  format_func=get_cat_display)

        type_opts = [T("all")] + (
            ["Expense", "Income"] if st.session_state.get('language_code') == 'EN' else ["支出", "收入"])
        sel_type = f2.selectbox(T("filter_type"), type_opts)

    # 筛选逻辑
    df_show = raw_df.copy()
    if sel_cats:
        df_show = df_show[df_show['category'].isin(sel_cats)]
    if sel_type != T("all"):
        df_show = df_show[df_show['type'] == sel_type]

    # UX 重点：使用 column_config 美化表格
    st.dataframe(
        df_show,
        use_container_width=True,
        hide_index=True,
        column_order=("date", "type", "category", "amount", "note", "id"),
        column_config={
            "id": st.column_config.NumberColumn("ID", help="Unique ID"),
            "date": st.column_config.DateColumn(T("date"), format="YYYY-MM-DD"),
            "type": st.column_config.TextColumn(T("type"), width="small"),
            "category": st.column_config.TextColumn(T("category"), width="medium"),
            "amount": st.column_config.NumberColumn(
                T("amount"),
                format=f"{CURRENCY} %.2f",  # 自动显示货币符号
                step=0.01
            ),
            "note": st.column_config.TextColumn(T("note"), width="large"),
        }
    )

    # 简化的删除功能
    st.divider()
    c_del1, c_del2 = st.columns([3, 1])
    with c_del1:
        # 创建易读的选项列表
        del_opts = {f"{r['date']} - {r['category']} - {r['amount']}": r['id'] for i, r in df_show.iterrows()}
        sel_rec_label = st.selectbox("Select to delete / 选择删除", options=list(del_opts.keys()),
                                     label_visibility="collapsed")
    with c_del2:
        if st.button("🗑️ " + T("tab_del"), type="secondary", use_container_width=True):
            if sel_rec_label:
                backend.delete_record(del_opts[sel_rec_label])
                st.rerun()