import streamlit as st

TRANS = {
    "app_title": {"CN": "我的账本", "EN": "My Ledger Pro"},
    "sidebar_title": {"CN": "📚 账本列表", "EN": "📚 Ledgers"},
    "current_ledger": {"CN": "当前账本", "EN": "Current Ledger"},
    "total_income": {"CN": "总收入", "EN": "Total Income"},
    "total_expense": {"CN": "总支出", "EN": "Total Expense"},
    "balance": {"CN": "结余", "EN": "Net Balance"},
    "header_entry": {"CN": "✨ 记一笔", "EN": "✨ New Transaction"},

    "date": {"CN": "日期", "EN": "Date"},
    "type": {"CN": "类型", "EN": "Type"},
    "category": {"CN": "分类", "EN": "Category"},
    "amount": {"CN": "金额", "EN": "Amount"},
    "note": {"CN": "备注", "EN": "Note"},

    "btn_save": {"CN": "💾 立即保存", "EN": "💾 Save Record"},

    "tab_overview": {"CN": "📊 概览", "EN": "📊 Dashboard"},
    "tab_stats": {"CN": "📅 统计日历", "EN": "📅 Calendar"},
    "tab_data": {"CN": "📋 明细", "EN": "📋 Records"},
    "tab_report": {"CN": "📑 财务报告", "EN": "📑 Reports"},

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
    "tab_del": {"CN": "删除记录", "EN": "Delete Record"},

    "report_type": {"CN": "报告类型", "EN": "Report Type"},
    "rep_weekly": {"CN": "周报 (Weekly)", "EN": "Weekly"},
    "rep_monthly": {"CN": "月报 (Monthly)", "EN": "Monthly"},
    "rep_yearly": {"CN": "年报 (Yearly)", "EN": "Yearly"},
    "sel_week": {"CN": "选择周 (点击该周任意一天)", "EN": "Select Week (Pick any day)"},
    "sel_month": {"CN": "选择月份 (点击该月任意一天)", "EN": "Select Month"},
    "sel_year": {"CN": "选择年份", "EN": "Select Year"},
    "gen_report": {"CN": "生成报告", "EN": "Generate Report"},
    "summary": {"CN": "汇总摘要", "EN": "Summary"},
    "cat_breakdown": {"CN": "分类详情", "EN": "Category Breakdown"},
    "download_excel": {"CN": "📥 导出 Excel 报告", "EN": "📥 Download Excel Report"}
}

# 1. 中文(纯文本) -> 英文(Emoji)
CAT_TRANS = {
    "餐饮": "🍔 Food",
    "交通": "🚗 Transport",
    "购物": "🛍️ Shopping",
    "居住": "🏠 Housing",
    "工资": "💰 Salary",
    "娱乐": "🎮 Fun",
    "医疗": "💊 Medical",
    "其他": "📦 Others"
}

# 2. 🔥 新增：中文(纯文本) -> 中文(Emoji)
# 这样中文模式下也能显示 Emoji 了！
CAT_CN_EMOJI = {
    "餐饮": "🍔 餐饮",
    "交通": "🚗 交通",
    "购物": "🛍️ 购物",
    "居住": "🏠 居住",
    "工资": "💰 工资",
    "娱乐": "🎮 娱乐",
    "医疗": "💊 医疗",
    "其他": "📦 其他"
}

# 反向映射：英文 -> 中文纯文本
CAT_TRANS_REV = {v: k for k, v in CAT_TRANS.items()}

def T(key):
    lang = st.session_state.get('language_code', 'EN')
    return TRANS.get(key, {}).get(lang, key)

def get_cat_display(cat_name):
    lang = st.session_state.get('language_code', 'CN')
    if lang == 'EN':
        return CAT_TRANS.get(cat_name, cat_name)
    else:
        # 🔥 修改这里：如果是中文，去查那个新的中文Emoji字典
        return CAT_CN_EMOJI.get(cat_name, cat_name)