import streamlit as st
import pandas as pd
import plotly.express as px
import backend
import lang_pack as lang
import calendar
from datetime import date, timedelta

# === 1. 页面配置 ===
st.set_page_config(
    page_title="My Ledger Pro",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="auto"
)

CURRENCY = "RM"
COLOR_MAP = {"收入": "#00CC96", "Income": "#00CC96", "支出": "#EF553B", "Expense": "#EF553B"}

# === 2. 核心 UI 样式 ===
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;}
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    div[data-testid="stMetric"] {
        background-color: #262730; 
        border: 1px solid #464b5c; 
        padding: 15px 20px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

    /* 日历样式 */
    .calendar-container { width: 100%; overflow-x: auto; }
    .cal-table { width: 100%; table-layout: fixed; border-collapse: separate; border-spacing: 0; }
    .cal-th { text-align: center; padding: 10px 0; font-size: 0.85rem; color: #a0a0a0; width: 14.28%; }
    .cal-td { padding: 4px; vertical-align: top; border: none !important; background: transparent !important; }
    .cal-card {
        background-color: #2d2d3a; border-radius: 12px; height: 95px; padding: 8px;
        display: flex; flex-direction: column; justify-content: space-between; align-items: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1); transition: all 0.2s ease;
    }
    .cal-card:hover { transform: translateY(-2px); background-color: #363645; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
    .cal-card.pos { background-color: #00C897; color: white; }
    .cal-card.neg { background-color: #FF5C5C; color: white; }
    .cal-card.today { border: 2px solid #FFD700; }
    .cal-day-num { font-size: 1rem; font-weight: 600; align-self: flex-start; }
    .cal-val { font-size: 0.85rem; font-weight: bold; align-self: flex-end; }
    .week-view .cal-card { height: 110px; }
    </style>
    """, unsafe_allow_html=True)


# === 3. 回调函数 ===
def save_callback():
    lang_code = st.session_state.get('language_code', 'CN')
    amt = st.session_state.get('input_amount', 0.0)
    cat = st.session_state.get(f'input_category_{lang_code}', "")
    typ = st.session_state.get('input_type', "")
    note = st.session_state.get('input_note', "")
    dt = st.session_state.get('input_date', date.today())
    active_id = st.session_state.get('active_ledger_id')

    if active_id and amt > 0 and cat:
        db_type = "Expense" if any(x in typ for x in ["支出", "Expense"]) else "Income"
        backend.save_record(active_id, dt, db_type, cat, amt, note)
        st.toast("✅ " + ("已保存!" if lang_code == 'CN' else "Saved Successfully!"))
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


# === 4. 日历函数 ===
def render_calendar_html(year, month, df_data, mode='Month', selected_date=None):
    daily_net = {}
    if not df_data.empty:
        df_calc = df_data.copy()
        inc_keys = ['收入', 'Income']
        df_calc['calc_amount'] = df_calc.apply(
            lambda x: x['amount'] if x['type'] in inc_keys else -x['amount'], axis=1
        )
        daily_net = df_calc.groupby('date')['calc_amount'].sum().to_dict()

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)

    if mode == 'Week':
        sel_dt = pd.to_datetime(selected_date).date()
        target_week = []
        for week in month_days:
            if sel_dt.day in week and week[week.index(sel_dt.day)] != 0:
                target_week = week
                break
        if not target_week:
            month_days = cal.monthdayscalendar(year, month)  # Fallback
        else:
            month_days = [target_week]

    week_days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    html = '<div class="calendar-container"><table class="cal-table"><thead><tr>'
    for w in week_days: html += f'<th class="cal-th">{w}</th>'
    html += '</tr></thead><tbody class="week-view" >' if mode == 'Week' else '<tbody>'
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
                if current_date_str == today_str: card_class += " today"

                val_display = ""
                if val != 0:
                    prefix = "+" if val > 0 else ""
                    val_display = f'<span class="cal-val">{prefix}{val:,.0f}</span>'
                html += f'<td class="cal-td"><div class="{card_class}"><span class="cal-day-num">{day}</span>{val_display}</div></td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    return html


# === 5. Sidebar & Main ===
backend.init_db()
all_ledgers = backend.get_ledgers()
ledger_names = [L[1] for L in all_ledgers]
ledger_map = {L[1]: L[0] for L in all_ledgers}

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2920/2920349.png", width=50)
    st.markdown("### " + lang.T("sidebar_title"))
    st.radio("Language", ["CN", "EN"], horizontal=True, label_visibility="collapsed", key="language_code")

    if ledger_names:
        selected_ledger_name = st.selectbox(lang.T("current_ledger"), ledger_names)
        current_ledger_id = ledger_map[selected_ledger_name]
        st.session_state['active_ledger_id'] = current_ledger_id
    else:
        st.warning("⚠️ No Ledgers")
        current_ledger_id = None
        selected_ledger_name = None

    st.divider()
    with st.expander(lang.T("settings")):
        new_ledger_name = st.text_input(lang.T("create_ledger"), key="new_ledger_input", placeholder="Name...")
        if st.button("➕", use_container_width=True):
            if new_ledger_name and new_ledger_name not in ledger_names:
                backend.add_ledger(new_ledger_name)
                st.rerun()
        if ledger_names:
            ledger_to_del = st.selectbox("Del Ledger", ledger_names, key="del_ledger_select")
            if st.button("🗑️", type="primary", use_container_width=True):
                backend.delete_ledger(ledger_map[ledger_to_del])
                st.rerun()

    if selected_ledger_name:
        with st.expander(lang.T("manage_cats")):
            current_categories = backend.get_categories(current_ledger_id)
            c1, c2 = st.tabs(["➕", "➖"])
            with c1:
                st.text_input("New", key='new_cat_input', label_visibility="collapsed")
                st.button("Add", on_click=add_cat_callback, use_container_width=True)
            with c2:
                st.selectbox("Del", current_categories, key='del_cat_select', label_visibility="collapsed")
                st.button("Remove", on_click=del_cat_callback, type="primary", use_container_width=True)

if selected_ledger_name:
    st.title(f"{selected_ledger_name}")
else:
    st.title(lang.T("app_title"))
    st.stop()

# 记账区
with st.expander(lang.T("header_entry"), expanded=True):
    c1, c2, c3, c4 = st.columns([1.2, 1, 1.2, 1])
    with c1: st.date_input(lang.T("date"), date.today(), key='input_date')
    with c2:
        type_opts = ["支出", "收入"] if st.session_state.get('language_code') == 'CN' else ["Expense", "Income"]
        st.selectbox(lang.T("category"), type_opts, key='input_type', label_visibility="visible")
    with c3:
        current_cats = backend.get_categories(current_ledger_id)
        st.selectbox(lang.T("category"), current_cats, format_func=lang.get_cat_display,
                     key=f'input_category_{st.session_state.get("language_code")}')
    with c4: st.number_input(lang.T("amount"), min_value=0.0, step=1.0, format="%.2f", key='input_amount')
    st.text_input(lang.T("note"), key='input_note', placeholder="Note...")
    st.button(lang.T("btn_save"), on_click=save_callback, type="primary", use_container_width=True)

# =========================================================
# 🔥 修复：增强版全局数据翻译 (使用 replace 代替 map)
# =========================================================
raw_df = backend.get_all_records(current_ledger_id)

if not raw_df.empty:
    current_lang = st.session_state.get('language_code', 'CN')

    # 0. 清洗数据：去除可能存在的首尾空格，确保匹配成功
    raw_df['category'] = raw_df['category'].astype(str).str.strip()

    if current_lang == 'EN':
        # 1. Type 翻译
        raw_df['type'] = raw_df['type'].replace(['支出', 'Expense'], 'Expense')
        raw_df['type'] = raw_df['type'].replace(['收入', 'Income'], 'Income')

        # 2. Category 翻译 (使用 replace，没找到的保留原样)
        raw_df['category'] = raw_df['category'].replace(lang.CAT_TRANS)
    else:
        # CN 模式
        raw_df['type'] = raw_df['type'].replace(['Expense', '支出'], '支出')
        raw_df['type'] = raw_df['type'].replace(['Income', '收入'], '收入')
        raw_df['category'] = raw_df['category'].replace(lang.CAT_TRANS_REV)

# 选项卡
tab_overview, tab_stats, tab_data, tab_report = st.tabs(
    [lang.T("tab_overview"), lang.T("tab_stats"), lang.T("tab_data"), lang.T("tab_report")])

if raw_df.empty:
    st.info(lang.T("empty"))
    st.stop()

# === Tab 1: 概览 (修复饼图) ===
with tab_overview:
    inc_key = '收入' if current_lang == 'CN' else 'Income'
    exp_key = '支出' if current_lang == 'CN' else 'Expense'

    inc = raw_df[raw_df['type'] == inc_key]['amount'].sum()
    exp = raw_df[raw_df['type'] == exp_key]['amount'].sum()
    bal = inc - exp

    col1, col2, col3 = st.columns(3)
    col1.metric(lang.T("total_income"), f"{CURRENCY} {inc:,.2f}", delta="Income", delta_color="normal")
    col2.metric(lang.T("total_expense"), f"{CURRENCY} {exp:,.2f}", delta=f"-{exp:,.2f}", delta_color="normal")
    col3.metric(lang.T("balance"), f"{CURRENCY} {bal:,.2f}", delta=f"{bal:,.2f}", delta_color="normal")

    st.divider()
    c_chart1, c_chart2 = st.columns(2)
    with c_chart1:
        st.subheader("📊 " + ("收支构成" if current_lang == 'CN' else "Composition"))

        # 🔥 再次确保饼图数据是翻译过的
        df_pie = raw_df.copy()
        chart_data = df_pie.groupby('category')['amount'].sum().reset_index()

        fig_pie = px.pie(chart_data, values='amount', names='category', hole=0.5)
        st.plotly_chart(fig_pie, use_container_width=True)

    with c_chart2:
        st.subheader("📅 " + ("近期趋势" if current_lang == 'CN' else "Trend"))
        daily_trend = raw_df.groupby('date')['amount'].sum().reset_index()
        fig_line = px.area(daily_trend, x='date', y='amount')
        st.plotly_chart(fig_line, use_container_width=True)

# === Tab 2: 统计日历 ===
with tab_stats:
    cc1, cc2 = st.columns([1, 2])
    with cc1:
        v_mode_sel = st.radio(lang.T("cal_view"), [lang.T("view_month"), lang.T("view_week")], horizontal=True)
        mode_code = 'Month' if v_mode_sel == lang.T("view_month") else 'Week'
    with cc2: pick_date = st.date_input(lang.T("cal_date"), date.today())

    st.divider()
    cal_html = render_calendar_html(pick_date.year, pick_date.month, raw_df, mode=mode_code, selected_date=pick_date)
    st.markdown(cal_html, unsafe_allow_html=True)

    st.divider()
    df_viz = raw_df.copy()
    df_viz['month'] = pd.to_datetime(df_viz['date']).dt.to_period('M').astype(str)
    monthly_stats = df_viz.groupby(['month', 'type'])['amount'].sum().reset_index()
    fig_bar = px.bar(monthly_stats, x='month', y='amount', color='type', barmode='group', color_discrete_map=COLOR_MAP)
    st.plotly_chart(fig_bar, use_container_width=True)

# === Tab 3: 明细 ===
with tab_data:
    with st.expander(lang.T("filter_label"), expanded=False):
        f1, f2 = st.columns(2)
        available_cats = raw_df['category'].unique().tolist()
        sel_cats = f1.multiselect(lang.T("filter_cat"), available_cats)

        type_opts = [lang.T("all")] + (
            [lang.T("Expense"), lang.T("Income")] if current_lang == 'EN' else ["支出", "收入"])
        sel_type = f2.selectbox(lang.T("filter_type"), type_opts)

    df_show = raw_df.copy()
    if sel_cats: df_show = df_show[df_show['category'].isin(sel_cats)]
    if sel_type != lang.T("all"):
        target_type = sel_type
        df_show = df_show[df_show['type'] == target_type]

    st.dataframe(
        df_show,
        use_container_width=True,
        hide_index=True,
        column_order=("date", "type", "category", "amount", "note"),
        column_config={
            "date": st.column_config.DateColumn(lang.T("date"), format="YYYY-MM-DD"),
            "type": st.column_config.TextColumn(lang.T("type"), width="small"),
            "category": st.column_config.TextColumn(lang.T("category"), width="medium"),
            "amount": st.column_config.NumberColumn(lang.T("amount"), format=f"{CURRENCY} %.2f", step=0.01),
            "note": st.column_config.TextColumn(lang.T("note"), width="large"),
        }
    )

    c_del1, c_del2 = st.columns([3, 1])
    with c_del1:
        del_opts = {f"{r['date']} - {r['category']} - {r['amount']}": r['id'] for i, r in df_show.iterrows()}
        sel_rec_label = st.selectbox("Delete Record", options=list(del_opts.keys()), label_visibility="collapsed")
    with c_del2:
        if st.button("🗑️ " + lang.T("tab_del"), type="secondary", use_container_width=True):
            if sel_rec_label:
                backend.delete_record(del_opts[sel_rec_label])
                st.rerun()

# === Tab 4: 财务报告 ===
with tab_report:
    st.subheader(lang.T("report_type"))
    report_mode = st.radio("Mode", [lang.T("rep_weekly"), lang.T("rep_monthly"), lang.T("rep_yearly")], horizontal=True,
                           label_visibility="collapsed")

    start_date, end_date = None, None
    filter_desc = ""

    c_rep1, c_rep2 = st.columns(2)
    with c_rep1:
        if report_mode == lang.T("rep_weekly"):
            sel_d = st.date_input(lang.T("sel_week"), date.today())
            start_date = sel_d - timedelta(days=sel_d.weekday())
            end_date = start_date + timedelta(days=6)
            filter_desc = f"Week: {start_date} ~ {end_date}"
        elif report_mode == lang.T("rep_monthly"):
            sel_d = st.date_input(lang.T("sel_month"), date.today())
            start_date = sel_d.replace(day=1)
            next_month = start_date.replace(day=28) + timedelta(days=4)
            end_date = next_month - timedelta(days=next_month.day)
            filter_desc = f"Month: {start_date.strftime('%Y-%m')}"
        elif report_mode == lang.T("rep_yearly"):
            sel_year = st.selectbox(lang.T("sel_year"), range(date.today().year, 2020, -1))
            start_date = date(sel_year, 1, 1)
            end_date = date(sel_year, 12, 31)
            filter_desc = f"Year: {sel_year}"

    if start_date and end_date:
        mask = (pd.to_datetime(raw_df['date']).dt.date >= start_date) & (
                    pd.to_datetime(raw_df['date']).dt.date <= end_date)
        rep_df = raw_df[mask].copy()

        st.divider()
        st.markdown(f"### 📄 {filter_desc}")

        if not rep_df.empty:
            inc_k = '收入' if current_lang == 'CN' else 'Income'
            exp_k = '支出' if current_lang == 'CN' else 'Expense'

            r_inc = rep_df[rep_df['type'] == inc_k]['amount'].sum()
            r_exp = rep_df[rep_df['type'] == exp_k]['amount'].sum()
            r_bal = r_inc - r_exp

            rc1, rc2, rc3 = st.columns(3)
            rc1.metric(lang.T("total_income"), f"{CURRENCY} {r_inc:,.2f}")
            rc2.metric(lang.T("total_expense"), f"{CURRENCY} {r_exp:,.2f}")
            rc3.metric(lang.T("balance"), f"{CURRENCY} {r_bal:,.2f}")

            st.subheader(lang.T("cat_breakdown"))

            # 报告页分类翻译修复
            cat_summary = rep_df.groupby(['category', 'type'])['amount'].sum().reset_index().sort_values('amount',
                                                                                                         ascending=False)

            st.dataframe(
                cat_summary,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "category": st.column_config.TextColumn(lang.T("category")),
                    "type": st.column_config.TextColumn(lang.T("type")),
                    "amount": st.column_config.NumberColumn(lang.T("amount"), format=f"{CURRENCY} %.2f")
                }
            )

            st.subheader(lang.T("tab_data"))
            st.dataframe(
                rep_df,
                use_container_width=True,
                hide_index=True,
                column_order=("date", "type", "category", "amount", "note"),
                column_config={
                    "date": st.column_config.DateColumn(lang.T("date"), format="YYYY-MM-DD"),
                    "type": st.column_config.TextColumn(lang.T("type")),
                    "category": st.column_config.TextColumn(lang.T("category")),
                    "amount": st.column_config.NumberColumn(lang.T("amount"), format=f"{CURRENCY} %.2f"),
                    "note": st.column_config.TextColumn(lang.T("note"))
                }
            )

            clean_export_df = rep_df[['date', 'type', 'category', 'amount', 'note']]
            excel_data = backend.to_excel(clean_export_df)

            st.download_button(
                label=f"{lang.T('download_excel')}",
                data=excel_data,
                file_name=f'Report_{start_date}_{end_date}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                type='primary'
            )
        else:
            st.info("No data in this period.")