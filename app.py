import streamlit as st
import pandas as pd
import plotly.express as px
import backend
import calendar
from datetime import date

# === 1. 页面配置 ===
st.set_page_config(
    page_title="My Ledger Pro",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="auto"
)

CURRENCY = "RM"

# === 2. 核心 UI 样式优化 ===
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;}
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    /* Metric 卡片样式 */
    div[data-testid="stMetric"] {
        background-color: #262730; 
        border: 1px solid #464b5c; 
        padding: 15px 20px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.3);
        border-color: #808495;
    }

    button[data-baseweb="tab"] {
        font-size: 16px;
        font-weight: 600;
    }

    /* === 日历组件样式 === */
    .calendar-container {
        width: 100%;
        overflow-x: auto;
    }
    .cal-table {
        width: 100%;
        table-layout: fixed;
        border-collapse: separate; 
        border-spacing: 0; 
    }
    .cal-th {
        text-align: center;
        padding: 10px 0;
        font-size: 0.85rem;
        color: #a0a0a0;
        font-weight: 600;
        text-transform: uppercase;
        width: 14.28%;
    }
    .cal-td {
        padding: 4px;
        vertical-align: top;
        border: none !important;
        background: transparent !important;
    }
    .cal-card {
        background-color: #2d2d3a;
        border-radius: 12px;
        height: 95px;
        padding: 8px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
    }
    .cal-card:hover {
        transform: translateY(-2px);
        background-color: #363645;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .cal-card.pos {
        background-color: #00C897;
        color: white;
        box-shadow: 0 4px 10px rgba(0, 200, 151, 0.3);
    }
    .cal-card.neg {
        background-color: #FF5C5C;
        color: white;
        box-shadow: 0 4px 10px rgba(255, 92, 92, 0.3);
    }
    .cal-card.today {
        border: 2px solid #FFD700;
    }
    .cal-day-num {
        font-size: 1rem;
        font-weight: 600;
        align-self: flex-start;
    }
    .cal-val {
        font-size: 0.85rem;
        font-weight: bold;
        align-self: flex-end;
    }
    .week-view .cal-card { height: 110px; }
    </style>
    """, unsafe_allow_html=True)

# === 3. 语言包与映射 ===
TRANS = {
    "app_title": {"CN": "我的账本", "EN": "My Ledger Pro"},
    "sidebar_title": {"CN": "📚 账本列表", "EN": "📚 Ledgers"},
    "current_ledger": {"CN": "当前账本", "EN": "Current Ledger"},
    "total_income": {"CN": "总收入", "EN": "Total Income"},
    "total_expense": {"CN": "总支出", "EN": "Total Expense"},
    "balance": {"CN": "结余", "EN": "Net Balance"},
    "header_entry": {"CN": "✨ 记一笔", "EN": "✨ New Transaction"},
    "date": {"CN": "日期", "EN": "Date"},
    "category": {"CN": "分类", "EN": "Category"},
    "amount": {"CN": "金额", "EN": "Amount"},
    "note": {"CN": "备注", "EN": "Note"},
    "btn_save": {"CN": "💾 立即保存", "EN": "💾 Save Record"},
    "tab_overview": {"CN": "📊 概览", "EN": "📊 Dashboard"},
    "tab_stats": {"CN": "📅 统计日历", "EN": "📅 Calendar & Stats"},
    "tab_data": {"CN": "📋 明细", "EN": "📋 Records"},
    "filter_label": {"CN": "🔍 筛选与搜索", "EN": "🔍 Filter & Search"},
    "filter_cat": {"CN": "按分类", "EN": "By Category"},
    "filter_type": {"CN": "按类型", "EN": "By Type"},
    "all": {"CN": "全部", "EN": "All"},
    "settings": {"CN": "⚙️ 设置", "EN": "⚙️ Settings"},
    "create_ledger": {"CN": "创建新账本", "EN": "Create Ledger"},
    "manage_cats": {"CN": "分类管理", "EN": "Categories"},
    "welcome": {"CN": "欢迎回来！", "EN": "Welcome Back!"},
    "empty": {"CN": "暂无数据，快去记一笔吧！", "EN": "No records yet. Add one now!"},
    "cal_view": {"CN": "视图模式", "EN": "View Mode"},
    "view_month": {"CN": "月视图", "EN": "Month"},
    "view_week": {"CN": "周视图", "EN": "Week"},
    "cal_date": {"CN": "选择日期", "EN": "Select Date"},
    "tab_del":{"CN":"删除记录","EN":"Delete Record"}
}

# 这里的 Key 是数据库里的中文，Value 是英文显示
CAT_TRANS = {
    "餐饮": "🍔 Food", "交通": "🚗 Transport", "购物": "🛍️ Shopping",
    "居住": "🏠 Housing", "工资": "💰 Salary", "娱乐": "🎮 Fun",
    "医疗": "💊 Medical", "其他": "📦 Others"
}


def T(key):
    lang = st.session_state.get('language_code', 'EN')
    return TRANS.get(key, {}).get(lang, key)


def get_cat_display(cat_name):
    """单独显示分类时的翻译辅助"""
    lang = st.session_state.get('language_code', 'CN')
    if lang == 'EN': return CAT_TRANS.get(cat_name, cat_name)
    return cat_name


COLOR_MAP = {"收入": "#00CC96", "Income": "#00CC96", "支出": "#EF553B", "Expense": "#EF553B"}


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
        # 存入数据库时，统一转成标准的中文或英文（这里假设存中文逻辑不变，或者存当前界面语言）
        # 为了兼容性，我们根据 type_opts 的选择来判断
        db_type = "Expense" if any(x in typ for x in ["支出", "Expense"]) else "Income"

        # 如果是英文模式下选的 "Food"，我们需要存入数据库什么？
        # 建议：数据库存什么就是什么。如果用户在英文界面存了 "Food"，那就存 "Food"。
        # 但为了让旧数据 "餐饮" 和新数据 "Food" 混在一起能看，我们通常在读取时翻译。
        # 这里为了简单，直接存。

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


# === 5. 日历生成函数 ===
def render_calendar_html(year, month, df_data, mode='Month', selected_date=None):
    daily_net = {}
    if not df_data.empty:
        # 此时 df_data 已经是翻译过的了，所以要判断 Income/Expense
        df_calc = df_data.copy()
        # 兼容中文和英文的判断
        df_calc['calc_amount'] = df_calc.apply(
            lambda x: x['amount'] if x['type'] in ['收入', 'Income'] else -x['amount'], axis=1
        )
        daily_net = df_calc.groupby('date')['calc_amount'].sum().to_dict()

    cal = calendar.Calendar(firstweekday=6)

    if mode == 'Month':
        month_days = cal.monthdayscalendar(year, month)
    else:
        sel_dt = pd.to_datetime(selected_date).date()
        all_weeks = cal.monthdayscalendar(year, month)
        target_week = []
        found = False
        for week in all_weeks:
            if sel_dt.day in week and week[week.index(sel_dt.day)] != 0:
                target_week = week
                found = True
                break
        if not found:
            month_days = all_weeks
        else:
            month_days = [target_week]

    week_days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    html = '<div class="calendar-container"><table class="cal-table">'

    html += '<thead><tr>'
    for w in week_days:
        html += f'<th class="cal-th">{w}</th>'
    html += '</tr></thead>'

    html += '<tbody class="week-view" >' if mode == 'Week' else '<tbody>'
    today_str = str(date.today())

    for week in month_days:
        html += '<tr>'
        for day in week:
            if day == 0:
                html += '<td class="cal-td"></td>'
            else:
                current_date_str = f"{year}-{month:02d}-{day:02d}"
                val = daily_net.get(current_date_str, 0)

                card_class = "cal-card"
                if val > 0:
                    card_class += " pos"
                elif val < 0:
                    card_class += " neg"

                if current_date_str == today_str:
                    card_class += " today"

                val_display = ""
                if val != 0:
                    prefix = "+" if val > 0 else ""
                    val_display = f'<span class="cal-val">{prefix}{val:,.0f}</span>'

                html += '<td class="cal-td">'
                html += f'<div class="{card_class}">'
                html += f'<span class="cal-day-num">{day}</span>'
                html += val_display
                html += '</div>'
                html += '</td>'
        html += '</tr>'

    html += '</tbody></table></div>'
    return html


# === 6. 程序入口 ===
backend.init_db()
all_ledgers = backend.get_ledgers()
ledger_names = [L[1] for L in all_ledgers]
ledger_map = {L[1]: L[0] for L in all_ledgers}

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2920/2920349.png", width=50)
    st.markdown("### " + T("sidebar_title"))
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
    with st.expander(T("settings")):
        st.caption(T("create_ledger"))
        new_ledger_name = st.text_input("Name", key="new_ledger_input", label_visibility="collapsed",
                                        placeholder="New Ledger Name")
        if st.button("➕ " + T("create_ledger"), use_container_width=True):
            if new_ledger_name and new_ledger_name not in ledger_names:
                backend.add_ledger(new_ledger_name)
                st.rerun()
        st.divider()
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

if selected_ledger_name:
    st.title(f"{selected_ledger_name}")
else:
    st.title(T("app_title"))
    st.stop()

# 记账区
with st.expander(T("header_entry"), expanded=True):
    c1, c2, c3, c4 = st.columns([1.2, 1, 1.2, 1])
    with c1: st.date_input(T("date"), date.today(), key='input_date')
    with c2:
        type_opts = ["支出", "收入"] if st.session_state.get('language_code') == 'CN' else ["Expense", "Income"]
        st.selectbox(T("category"), type_opts, key='input_type', label_visibility="visible")
    with c3:
        current_cats = backend.get_categories(current_ledger_id)
        # 记账时，下拉菜单也显示翻译后的
        st.selectbox(T("category"), current_cats, format_func=get_cat_display,
                     key=f'input_category_{st.session_state.get("language_code")}')
    with c4: st.number_input(T("amount"), min_value=0.0, step=1.0, format="%.2f", key='input_amount')
    st.text_input(T("note"), key='input_note', placeholder="e.g. Lunch with friends...")
    st.button(T("btn_save"), on_click=save_callback, type="primary", use_container_width=True)

# === 核心逻辑：获取数据并根据语言进行“翻译” ===
raw_df = backend.get_all_records(current_ledger_id)

# 如果是英文模式，我们在此处对 DataFrame 进行“原地翻译”
# 这样后续的表格、图表、日历都会自动使用英文
if st.session_state.get('language_code') == 'EN' and not raw_df.empty:
    # 1. 翻译类型 (Type)
    type_mapping = {'收入': 'Income', '支出': 'Expense'}
    raw_df['type'] = raw_df['type'].map(type_mapping).fillna(raw_df['type'])

    # 2. 翻译分类 (Category) - 仅翻译系统预设的，自定义的保留原样
    # map(CAT_TRANS) 会把匹配到的转英文，匹配不到的变成 NaN
    # fillna(raw_df['category']) 会把 NaN 的地方填回原来的中文
    raw_df['category'] = raw_df['category'].map(CAT_TRANS).fillna(raw_df['category'])

# 选项卡
tab_overview, tab_stats, tab_data = st.tabs([T("tab_overview"), T("tab_stats"), T("tab_data")])

if raw_df.empty:
    st.info(T("empty"))
    st.stop()

# === Tab 1: 概览 ===
with tab_overview:
    inc = raw_df[raw_df['type'].isin(['收入', 'Income'])]['amount'].sum()
    exp = raw_df[raw_df['type'].isin(['支出', 'Expense'])]['amount'].sum()
    bal = inc - exp

    col1, col2, col3 = st.columns(3)
    col1.metric(T("total_income"), f"{CURRENCY} {inc:,.2f}", delta="Income", delta_color="normal")
    col2.metric(T("total_expense"), f"{CURRENCY} {exp:,.2f}", delta=f"-{exp:,.2f}", delta_color="normal")
    col3.metric(T("balance"), f"{CURRENCY} {bal:,.2f}", delta=f"{bal:,.2f}", delta_color="normal")

    st.divider()
    c_chart1, c_chart2 = st.columns(2)
    with c_chart1:
        st.subheader("📊 " + ("收支构成" if st.session_state.get('language_code') == 'CN' else "Composition"))
        chart_data = raw_df.groupby('category')['amount'].sum().reset_index()
        fig_pie = px.pie(chart_data, values='amount', names='category', hole=0.5)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)
    with c_chart2:
        st.subheader("📅 " + ("近期趋势" if st.session_state.get('language_code') == 'CN' else "Recent Trend"))
        daily_trend = raw_df.groupby('date')['amount'].sum().reset_index()
        fig_line = px.area(daily_trend, x='date', y='amount', color_discrete_sequence=['#636EFA'])
        fig_line.update_layout(margin=dict(t=0, b=0, l=0, r=0), yaxis_title=None, xaxis_title=None)
        st.plotly_chart(fig_line, use_container_width=True)

# === Tab 2: 统计日历 ===
with tab_stats:
    cc1, cc2 = st.columns([1, 2])
    with cc1:
        v_mode_label = [T("view_month"), T("view_week")]
        v_mode_sel = st.radio(T("cal_view"), v_mode_label, horizontal=True)
        mode_code = 'Month' if v_mode_sel == T("view_month") else 'Week'
    with cc2:
        pick_date = st.date_input(T("cal_date"), date.today())

    st.divider()
    # 传入已经翻译过的 raw_df，所以日历不需要自己再翻译
    cal_html = render_calendar_html(pick_date.year, pick_date.month, raw_df, mode=mode_code, selected_date=pick_date)
    st.markdown(cal_html, unsafe_allow_html=True)

    st.divider()
    st.subheader("📈 " + T("tab_stats"))

    df_viz = raw_df.copy()
    df_viz['month'] = pd.to_datetime(df_viz['date']).dt.to_period('M').astype(str)
    monthly_stats = df_viz.groupby(['month', 'type'])['amount'].sum().reset_index()

    fig_bar = px.bar(
        monthly_stats, x='month', y='amount', color='type',
        barmode='group', text_auto='.2s', color_discrete_map=COLOR_MAP
    )
    fig_bar.update_layout(xaxis_title="", yaxis_title="", margin=dict(t=10, b=0, l=0, r=0))
    st.plotly_chart(fig_bar, use_container_width=True)

# === Tab 3: 明细与筛选 ===
with tab_data:
    with st.expander(T("filter_label"), expanded=False):
        f1, f2 = st.columns(2)

        # 修复：筛选框的选项也必须是翻译过的
        # 直接从 dataframe 获取当前存在的分类，而不是从 backend 拿原始分类
        # 这样能保证筛选框里的选项和表格里的内容一致（都是英文或都是中文）
        available_cats = raw_df['category'].unique().tolist()
        sel_cats = f1.multiselect(T("filter_cat"), available_cats)

        type_opts = [T("all")] + (
            ["Expense", "Income"] if st.session_state.get('language_code') == 'EN' else ["支出", "收入"])
        sel_type = f2.selectbox(T("filter_type"), type_opts)

    df_show = raw_df.copy()
    if sel_cats: df_show = df_show[df_show['category'].isin(sel_cats)]
    if sel_type != T("all"): df_show = df_show[df_show['type'] == sel_type]

    st.dataframe(
        df_show,
        use_container_width=True, hide_index=True,
        column_order=("date", "type", "category", "amount", "note", "id"),
        column_config={
            "id": st.column_config.NumberColumn("ID"),
            "date": st.column_config.DateColumn(T("date"), format="YYYY-MM-DD"),
            "type": st.column_config.TextColumn(T("type"), width="small"),
            "category": st.column_config.TextColumn(T("category"), width="medium"),
            "amount": st.column_config.NumberColumn(T("amount"), format=f"{CURRENCY} %.2f", step=0.01),
            "note": st.column_config.TextColumn(T("note"), width="large"),
        }
    )
    st.divider()
    c_del1, c_del2 = st.columns([3, 1])
    with c_del1:
        del_opts = {f"{r['date']} - {r['category']} - {r['amount']}": r['id'] for i, r in df_show.iterrows()}
        sel_rec_label = st.selectbox("Select to delete", options=list(del_opts.keys()), label_visibility="collapsed")
    with c_del2:
        if st.button("🗑️ " + T("tab_del"), type="secondary", use_container_width=True):
            if sel_rec_label:
                backend.delete_record(del_opts[sel_rec_label])
                st.rerun()