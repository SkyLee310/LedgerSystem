import streamlit as st
import pandas as pd
import plotly.express as px
import backend
from datetime import date, timedelta

# === 1. 页面配置 ===
# 必须是第一个 Streamlit 命令
st.set_page_config(
    page_title="My Ledger System",
    page_icon="📓",
    layout="wide",
    initial_sidebar_state="auto"  # 手机自动收起，电脑自动展开
)

CURRENCY = "RM"

TRANS = {
    # 侧边栏 & 标题
    "app_title": {"CN": "账本系统", "EN": "My Ledger System"},
    "sidebar_title": {"CN": "📚 账本", "EN": "📚 Ledger"},
    "lang_select": {"CN": "语言 / Language", "EN": "Language / 语言"},
    "current_ledger": {"CN": "📖 当前账本", "EN": "📖 Current Ledger"},

    # 账本设置
    "ledger_settings": {"CN": "⚙️ 账本设置 (新增/删除)", "EN": "⚙️ Ledger Settings"},
    "tab_add": {"CN": "新增", "EN": "Add"},
    "tab_del": {"CN": "删除", "EN": "Delete"},
    "input_new_ledger": {"CN": "输入新账本名称", "EN": "New Ledger Name"},
    "btn_create_ledger": {"CN": "创建新账本", "EN": "Create Ledger"},
    "warn_del_ledger": {"CN": "⚠️ 高危操作：删除账本将永久清除该账本下的所有数据！",
                        "EN": "⚠️ Danger: Deleting a ledger will wipe all its data!"},
    "select_del_ledger": {"CN": "选择要删除的账本", "EN": "Select Ledger to Delete"},
    "confirm_del_check": {"CN": "我确认要删除", "EN": "I confirm to delete"},
    "btn_del_ledger": {"CN": "🔴 确认删除账本", "EN": "🔴 Delete Ledger"},

    # 记账输入
    "header_entry": {"CN": "📝 记一笔", "EN": "📝 New Transaction"},
    "date": {"CN": "日期", "EN": "Date"},
    "type": {"CN": "类型", "EN": "Type"},
    "category": {"CN": "分类", "EN": "Category"},
    "amount": {"CN": "金额", "EN": "Amount"},
    "note": {"CN": "备注", "EN": "Note"},
    "btn_save": {"CN": "💾 保存记录", "EN": "💾 Save Record"},
    "msg_saved": {"CN": "✅ 已保存！", "EN": "✅ Saved!"},
    "msg_amount_error": {"CN": "⚠️ 金额必须大于 0", "EN": "⚠️ Amount must be > 0"},
    "msg_no_cat": {"CN": "请先添加分类", "EN": "Please add category first"},

    # 分类管理
    "cat_manage": {"CN": "🏷️ 分类管理 (新增/撤销)", "EN": "🏷️ Categories"},
    "input_new_cat": {"CN": "新分类名", "EN": "New Category Name"},
    "btn_add_cat": {"CN": "确认添加", "EN": "Add Category"},
    "select_del_cat": {"CN": "撤销分类", "EN": "Remove Category"},
    "btn_del_cat": {"CN": "确认删除", "EN": "Delete Category"},
    "msg_cat_added": {"CN": "分类已添加", "EN": "Category Added"},
    "msg_cat_deleted": {"CN": "分类已删除", "EN": "Category Deleted"},

    # 主看板
    "dashboard_title": {"CN": "财务看板", "EN": "Dashboard"},
    "tab_overview": {"CN": "📊 账本概览", "EN": "📊 Overview"},
    "tab_export": {"CN": "📥 数据导出", "EN": "📥 Export"},

    # 筛选与统计
    "filter_expand": {"CN": "🔍 筛选数据", "EN": "🔍 Filter Data"},
    "filter_cat": {"CN": "分类筛选", "EN": "Filter by Category"},
    "filter_type": {"CN": "类型筛选", "EN": "Filter by Type"},
    "total_income": {"CN": "总收入", "EN": "Total Income"},
    "total_expense": {"CN": "总支出", "EN": "Total Expense"},
    "balance": {"CN": "结余", "EN": "Balance"},
    "all": {"CN": "全部", "EN": "All"},

    # 图表与列表
    "header_list": {"CN": "📋 账本明细", "EN": "📋 Transactions"},
    "header_chart": {"CN": "📊 分布", "EN": "📊 Distribution"},
    "no_expense": {"CN": "无支出数据", "EN": "No Expense Data"},
    "del_record_expand": {"CN": "🗑️ 删除某条记录", "EN": "🗑️ Delete Record"},
    "select_record": {"CN": "选择记录", "EN": "Select Record"},
    "btn_del_record": {"CN": "删除选中项", "EN": "Delete Selected"},
    "empty_ledger": {"CN": "账本还是空的，快去记一笔吧！", "EN": "Ledger is empty, add a record!"},

    # 导出
    "header_export": {"CN": "📥 导出当前账本", "EN": "📥 Export Ledger"},
    "start_date": {"CN": "开始", "EN": "Start"},
    "end_date": {"CN": "结束", "EN": "End"},
    "found_records": {"CN": "共找到 {} 条记录", "EN": "Found {} records"},
    "btn_download": {"CN": "⬇️ 下载 Excel", "EN": "⬇️ Download Excel"},

    # 通用词汇
    "Income": {"CN": "收入", "EN": "Income"},
    "Expense": {"CN": "支出", "EN": "Expense"},

    # === 统计页面 ===
    "tab_stats": {"CN": "📈 数据统计", "EN": "📈 Statistics"},
    "chart_trend": {"CN": "📅 收支趋势 (按月)", "EN": "📅 Monthly Trend"},
    "chart_rank": {"CN": "🏆 支出排行榜", "EN": "🏆 Expense Ranking"},
}

CAT_TRANS = {
    "餐饮": "Food & Dining",
    "交通": "Transport",
    "购物": "Shopping",
    "居住": "Housing",
    "工资": "Salary",
    "娱乐": "Entertainment",
    "医疗": "Medical",
    "其他": "Others"
}


def T(key):
    lang = st.session_state.get('language_code', 'EN')
    if key in TRANS:
        return TRANS[key][lang]
    return key


def get_cat_display(cat_name):
    lang = st.session_state.get('language_code', 'CN')
    if lang == 'EN':
        return CAT_TRANS.get(cat_name, cat_name)
    else:
        return cat_name


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
        st.success("Saved!")
    elif amt <= 0:
        st.error("Amount must be > 0")
    else:
        st.error("Please check inputs")


def add_cat_callback():
    new_c = st.session_state.get('new_cat_input')
    active_id = st.session_state.get('active_ledger_id')
    if active_id and new_c and backend.add_category(active_id, new_c):
        st.toast(f"{T('msg_cat_added')}: {new_c}")
        st.session_state['new_cat_input'] = ""


def del_cat_callback():
    del_c = st.session_state.get('del_cat_select')
    active_id = st.session_state.get('active_ledger_id')
    if active_id and del_c:
        backend.delete_category(active_id, del_c)
        st.toast(f"{T('msg_cat_deleted')}: {del_c}")


# === 2. 安全的 CSS 样式 ===
# 只隐藏 footer 和 hamburger，但不隐藏 header 整体
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;} 
            footer {visibility: hidden;}
            /* header {visibility: hidden;}  <-- 这一行已被永久移除 */

            .block-container {
                padding-top: 2rem;
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

backend.init_db()

all_ledgers = backend.get_ledgers()
ledger_names = [L[1] for L in all_ledgers]
ledger_map = {L[1]: L[0] for L in all_ledgers}

# === 3. Sidebar 内容 ===
with st.sidebar:
    st.radio("🌐 Language", ["CN", "EN"], horizontal=True, key="language_code")
    st.divider()

    st.title(T("sidebar_title"))

    selected_ledger_name = None
    if ledger_names:
        selected_ledger_name = st.selectbox(T("current_ledger"), ledger_names)
        current_ledger_id = ledger_map[selected_ledger_name]
        st.session_state['active_ledger_id'] = current_ledger_id
    else:
        st.warning("No Ledgers Found / 未找到账本")

    with st.expander(T("ledger_settings")):
        l_tab1, l_tab2 = st.tabs([T("tab_add"), T("tab_del")])

        with l_tab1:
            new_ledger_name = st.text_input(T("input_new_ledger"), key="new_ledger_input")
            if st.button(T("btn_create_ledger")):
                if new_ledger_name and new_ledger_name not in ledger_names:
                    if backend.add_ledger(new_ledger_name):
                        st.success("OK")
                        st.rerun()
                elif new_ledger_name in ledger_names:
                    st.error("Exists / 已存在")

        with l_tab2:
            st.warning(T("warn_del_ledger"))
            if ledger_names:
                ledger_to_del = st.selectbox(T("select_del_ledger"), ledger_names, key="del_ledger_select")
                confirm_text = f"{T('confirm_del_check')} '{ledger_to_del}'"
                confirm_del = st.checkbox(confirm_text, key="del_confirm")

                if st.button(T("btn_del_ledger"), disabled=not confirm_del):
                    del_id = ledger_map[ledger_to_del]
                    success, msg = backend.delete_ledger(del_id)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    st.divider()

    if selected_ledger_name:
        with st.expander(T("cat_manage")):
            current_categories = backend.get_categories(current_ledger_id)
            c_tab1, c_tab2 = st.tabs([T("tab_add"), T("tab_del")])
            with c_tab1:
                st.text_input(T("input_new_cat"), key='new_cat_input')
                st.button(T("btn_add_cat"), on_click=add_cat_callback)
            with c_tab2:
                st.selectbox(T("select_del_cat"), current_categories, key='del_cat_select')
                st.button(T("btn_del_cat"), on_click=del_cat_callback)

# === 4. 主界面标题逻辑 ===
if 'active_ledger_id' in st.session_state:
    # 重新获取最新的账本列表以确保名称对应正确
    all_ledgers = backend.get_ledgers()
    ledger_map_rev = {L[0]: L[1] for L in all_ledgers}
    current_name = ledger_map_rev.get(st.session_state.active_ledger_id, "")
    st.title(f"💰 {current_name} - {T('dashboard_title')}")
else:
    st.title(T("app_title"))

if not selected_ledger_name:
    st.info("Please create a ledger in the sidebar first. / 请先在侧边栏创建一个账本。")
    st.stop()

# === 5. 记账输入框 ===
with st.expander(T("header_entry"), expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        st.date_input(T("date") if "date" in TRANS else "日期", date.today(), key='input_date')

        type_opts = ["支出", "收入"]
        if st.session_state.get('language_code') == 'EN':
            type_opts = ["Expense", "Income"]
        st.selectbox(T("category"), type_opts, key='input_type')

    with c2:
        current_categories = backend.get_categories(current_ledger_id)
        current_lang = st.session_state.get('language_code', 'CN')
        st.selectbox(
            T("category"),
            current_categories,
            format_func=get_cat_display,
            key=f'input_category_{current_lang}'
        )
        st.number_input(T("amount"), min_value=0.0, step=0.01, format="%.2f", key='input_amount')

    st.text_input(T("note"), key='input_note')
    st.button(T("btn_save"), on_click=save_callback, use_container_width=True, type="primary")

# === 6. 数据看板 Tabs ===
tab1, tab2, tab3 = st.tabs([T("tab_overview"), T("tab_stats"), T("tab_export")])

with tab1:
    raw_df = backend.get_all_records(current_ledger_id)

    if not raw_df.empty:
        with st.expander(T("filter_expand"), expanded=False):
            col1, col2 = st.columns([2, 1])
            with col1:
                all_cats = backend.get_categories(current_ledger_id)
                sel_cats = st.multiselect(
                    T("filter_cat"),
                    all_cats,
                    default=[],
                    format_func=get_cat_display,
                    placeholder=T("filter_cat")
                )
            with col2:
                type_filter_opts = [T("all")] + (
                    ["Expense", "Income"] if st.session_state.get('language_code') == 'EN' else ["支出", "收入"])
                sel_type = st.selectbox(T("filter_type"), type_filter_opts)

        df = raw_df.copy()

        exp_mask = df['type'].isin(['支出', 'Expense'])
        inc_mask = df['type'].isin(['收入', 'Income'])

        if st.session_state.get('language_code') == 'EN':
            df.loc[exp_mask, 'type'] = "Expense"
            df.loc[inc_mask, 'type'] = "Income"
            df['category'] = df['category'].map(CAT_TRANS).fillna(df['category'])
        else:
            df.loc[exp_mask, 'type'] = "支出"
            df.loc[inc_mask, 'type'] = "收入"

        if sel_cats:
            df = df[df['category'].isin(sel_cats)]

        if sel_type != T("all"):
            df = df[df['type'] == sel_type]

        inc = df[df['type'].isin(['收入', 'Income'])]['amount'].sum()
        exp = df[df['type'].isin(['支出', 'Expense'])]['amount'].sum()
        bal = inc - exp

        m1, m2, m3 = st.columns(3)
        m1.metric(T("total_income"), f"{CURRENCY} {inc:,.2f}")
        m2.metric(T("total_expense"), f"{CURRENCY} {exp:,.2f}")
        m3.metric(T("balance"), f"{CURRENCY} {bal:,.2f}")
        st.divider()

        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader(T("header_list"))
            st.dataframe(df[['date', 'type', 'category', 'amount', 'note']], use_container_width=True)

        with c2:
            st.subheader(T("header_chart"))
            exp_condition = df['type'].astype(str).str.contains('支出|Expense', case=False, na=False)
            exp_df = df[exp_condition]

            if not exp_df.empty:
                chart_data = exp_df.groupby('category')['amount'].sum().reset_index()
                fig = px.pie(chart_data, values='amount', names='category', hole=0.4)
                fig.update_layout(
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                    margin=dict(l=0, r=0, t=30, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(T("no_expense"))

        st.divider()

        with st.expander(T("del_record_expand")):
            del_opts = {f"{r['date']} | {r['category']} | {CURRENCY} {r['amount']:.2f}": r['id'] for i, r in
                        raw_df.iterrows()}
            if del_opts:
                sel_lbl = st.selectbox(T("select_record"), options=del_opts.keys())
                if st.button(T("btn_del_record")):
                    backend.delete_record(del_opts[sel_lbl])
                    st.success("OK")
                    st.rerun()
    else:
        st.info(T("empty_ledger"))

with tab2:
    st.subheader(T("chart_trend"))
    stat_df = backend.get_all_records(current_ledger_id)

    if not stat_df.empty:
        stat_df['month'] = pd.to_datetime(stat_df['date']).dt.to_period('M').astype(str)
        monthly_data = stat_df.groupby(['month', 'type'])['amount'].sum().reset_index()

        color_map = {
            "收入": "#2ecc71", "Income": "#2ecc71",
            "支出": "#e74c3c", "Expense": "#e74c3c"
        }

        fig_trend = px.bar(
            monthly_data, x='month', y='amount', color='type',
            barmode='group', color_discrete_map=color_map, text_auto='.2s',
            title="Monthly Income vs Expense"
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        st.divider()
        st.subheader(T("chart_rank"))

        exp_df = stat_df[stat_df['type'].astype(str).str.contains('支出|Expense', case=False)]
        if not exp_df.empty:
            cat_rank = exp_df.groupby('category')['amount'].sum().reset_index().sort_values('amount', ascending=True)
            if st.session_state.get('language_code') == 'EN':
                cat_rank['category'] = cat_rank['category'].map(CAT_TRANS).fillna(cat_rank['category'])

            fig_rank = px.bar(
                cat_rank, x='amount', y='category', orientation='h',
                text_auto='.2s', title="Top Expense Categories",
                color='amount', color_continuous_scale='Reds'
            )
            st.plotly_chart(fig_rank, use_container_width=True)
        else:
            st.info(T("no_expense"))
    else:
        st.info(T("empty_ledger"))

with tab3:
    st.subheader(T("header_export"))
    d1, d2 = st.columns(2)
    s_date = d1.date_input(T("start_date"), date.today() - timedelta(days=30))
    e_date = d2.date_input(T("end_date"), date.today())

    if s_date <= e_date:
        ex_df = backend.get_records_by_date_range(current_ledger_id, s_date, e_date)
        st.write(T("found_records").format(len(ex_df)))
        if not ex_df.empty:
            excel_data = backend.to_excel(ex_df)
            st.download_button(
                label=T("btn_download"),
                data=excel_data,
                file_name=f'{selected_ledger_name}_{s_date}_{e_date}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )