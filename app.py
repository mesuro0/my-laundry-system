import streamlit as st
import pandas as pd
import datetime
import os

# 設定網頁標題與寬螢幕排版
st.set_page_config(page_title="美舒容雲端洗衣管理系統", layout="wide")

# ==================== 🔐 安全密碼登入驗證 ====================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 歡迎使用洗衣店管理系統")
    st.subheader("本系統僅供店主與員工使用，請輸入管理密碼：")
    
    password = st.text_input("請輸入密碼：", type="password")
    login_btn = st.button("登入系統")
    
    if login_btn:
        if password == "1234":  
            st.session_state.authenticated = True
            st.success("✅ 密碼正確，正在登入...")
            st.rerun()
        else:
            st.error("❌ 密碼錯誤，請重新輸入！")
    st.stop()

# ==================== 🔓 登入成功後的系統主體 ====================
ORDERS_FILE = "laundry_orders.csv"
CUSTOMERS_FILE = "laundry_customers.csv"

# 預設衣服項目與基本計價 (對應舊系統衣服名稱功能)
PRICE_LIST = {
    "一般襯衫/T恤": 50,
    "長褲/牛仔褲": 60,
    "厚外套/大衣": 150,
    "床單/被套": 200,
    "毛毯/特殊材質": 300
}

# --- 初始化檔案與資料讀取 ---
if os.path.exists(ORDERS_FILE):
    df_orders = pd.read_csv(ORDERS_FILE)
    df_orders["手機號碼"] = df_orders["手機號碼"].astype(str)
else:
    df_orders = pd.DataFrame(columns=["訂單編號", "日期", "顧客姓名", "手機號碼", "衣服項目", "數量", "花色備註", "洗法備註", "前次餘額", "總金額", "目前狀態", "付款方式", "現有餘額"])

if os.path.exists(CUSTOMERS_FILE):
    df_cust = pd.read_csv(CUSTOMERS_FILE)
    df_cust["手機號碼"] = df_cust["手機號碼"].astype(str)
else:
    df_cust = pd.DataFrame(columns=["手機號碼", "顧客姓名", "性別", "儲值餘額", "折扣比率"])

if "receipt_data" not in st.session_state:
    st.session_state.receipt_data = None

# --- 輔助函式：取得客戶資訊 ---
def get_customer_info(phone):
    if df_cust.empty:
        return None, 0, 0
    match = df_cust[df_cust["手機號碼"] == str(phone)]
    if not match.empty:
        return match.iloc[0]["顧客姓名"], int(match.iloc[0]["儲值餘額"]), int(match.iloc[0]["折扣比率"])
    return None, 0, 0

# --- 核心功能分頁導覽（完美對應舊系統架構選單） ---
tab1, tab2, tab3, tab4 = st.tabs(["📥 洗衣作業 (收件與儲值)", "📋 清洗進度看板", "🔍 客戶資料維護", "📊 報表與查詢作業"])

# =====================================================================
# TAB 1: 洗衣作業 (新單收件與儲值開戶)
# =====================================================================
with tab1:
    col1, col2 = st.columns(2)
    
    # 左半邊：客戶資料維護(C) / 會員儲值功能
    with col1:
        st.header("💰 會員儲值與開戶維護")
        with st.form("deposit_form"):
            c_phone = st.text_input("會員手機號碼", placeholder="請輸入10碼手機").strip()
            c_name = st.text_input("會員姓名", placeholder="新會員請輸入姓名")
            c_gender = st.radio("性別", ["男", "女"], horizontal=True)
            c_discount = st.number_input("折扣比率 (%) (例如：填 10 代表打 9 折，無折扣填 0)", min_value=0, max_value=100, value=0, step=5)
            amount = st.number_input("儲值金額 (元)", min_value=0, value=0, step=100)
            deposit_btn = st.form_submit_button("執行儲值 / 開戶存檔")
            
            if deposit_btn:
                if not c_phone:
                    st.error("❌ 請輸入手機號碼")
                else:
                    if not df_cust.empty and str(c_phone) in df_cust["手機號碼"].values:
                        idx = df_cust[df_cust["手機號碼"] == str(c_phone)].index
                        df_cust.at[idx, "儲值餘額"] += amount
                        df_cust.at[idx, "折扣比率"] = c_discount
                        name_to_show = df_cust.at[idx, "顧客姓名"]
                        st.success(f"✅ 儲值成功！{name_to_show} 目前儲值餘額：${df_cust.at[idx, '儲值餘額']} 元")
                    else:
                        if not c_name:
                            st.error("❌ 新客戶請填寫姓名以進行建檔開戶")
                        else:
                            new_c = {"手機號碼": str(c_phone), "顧客姓名": c_name, "性別": c_gender, "儲值餘額": int(amount), "折扣比率": int(c_discount)}
                            df_cust = pd.concat([df_cust, pd.DataFrame([new_c])], ignore_index=True)
                            st.success(f"🎉 新增客戶成功！{c_name} 目前餘額：${amount} 元")
                    df_cust.to_csv(CUSTOMERS_FILE, index=False)
                    st.rerun()

    # 右半邊：門市收件作業(G)
    with col2:
        st.header("📥 門市收件作業")
        with st.form("order_form", clear_on_submit=True):
            o_phone = st.text_input("顧客手機號碼", placeholder="請輸入手機").strip()
            current_name, current_balance, current_discount = get_customer_info(o_phone)
            
            if o_phone and current_name:
                st.caption(f"💡 找到會員：{current_name} ｜ 當前儲值餘額：${current_balance} 元 ｜ 享折扣：{current_discount}%")
            elif o_phone:
                st.caption("⚠️ 此手機非儲值會員，結帳時將以【現金結帳】計算。")
                
            selected_item = st.selectbox("衣服種類", list(PRICE_LIST.keys()))
            quantity = st.number_input("數量", min_value=1, value=1, step=1)
            
            # 完美復刻舊系統「片語維護」快選單功能
            opt_color = st.selectbox("類別快選：花色/特徵", ["不分", "深色", "淺色", "白色", "黑色", "黃色", "藍色", "咖/卡其色", "紫/粉紅色"])
            opt_wash = st.selectbox("類別快選：洗法/配件", ["水洗", "乾洗", "燙衣", "其他", "拉大", "重處理"])
            
            pay_method = st.radio("付款方式設定", ["儲值金扣款", "現金結帳"], horizontal=True)
            
            # 自動計算計價與扣除折扣金額
            unit_price = PRICE_LIST[selected_item]
            subtotal = unit_price * quantity
            discount_amount = int(subtotal * (current_discount / 100))
            total_price = subtotal - discount_amount
            
            st.info(f"💰 計算：原價 ${subtotal} - 折扣比率省下 ${discount_amount} = 應收總金額: **${total_price}** 元")
            submit_btn = st.form_submit_button("確認入庫 (確定收件)")
            
            if submit_btn:
                if not o_phone:
                    st.error("❌ 請輸入手機號碼！")
                else:
                    can_order = True
                    cust_idx = df_cust[df_cust["手機號碼"] == str(o_phone)].index if not df_cust.empty else []
                    prev_balance = current_balance
                    
                    if pay_method == "儲值金扣款":
                        if len(cust_idx) == 0:
                            st.error("❌ 該手機非儲值會員，無法使用儲值扣款。請改選現金或先完成開戶。")
                            can_order = False
                        elif df_cust.at[cust_idx[0], "儲值餘額"] < total_price:
                            st.error(f"❌ 儲值餘額不足！目前僅剩 ${df_cust.at[cust_idx[0], '儲值餘額']} 元。")
                            can_order = False
                        else:
                            df_cust.at[cust_idx[0], "儲值餘額"] -= total_price
                            df_cust.to_csv(CUSTOMERS_FILE, index=False)
                    
                    if can_order:
                        final_name = df_cust.at[cust_idx[0], "顧客姓名"] if len(cust_idx) > 0 else "現場散客"
                        order_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                        today_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        _, updated_balance, _ = get_customer_info(o_phone)
                        
                        rem_bal_str = f"${updated_balance} 元" if len(cust_idx) > 0 else "散客不適用"
                        
                        new_order = {
                            "訂單編號": order_id, "日期": today_str, "顧客姓名": final_name,
                            "手機號碼": str(o_phone), "衣服項目": selected_item, "數量": quantity,
                            "花色備註": opt_color, "洗法備註": opt_wash, "前次餘額": prev_balance,
                            "總金額": total_price, "目前狀態": "待清洗", "付款方式": pay_method, "現有餘額": updated_balance
                        }
                        df_orders = pd.concat([df_orders, pd.DataFrame([new_order])], ignore_index=True)
                        df_orders.to_csv(ORDERS_FILE, index=False)
                        st.session_state.receipt_data = {
                            "id": order_id, "date": today_str, "name": final_name, "phone": o_phone,
                            "item": selected_item, "qty": quantity, "color": opt_color, "wash": opt_wash,
                            "total": total_price, "pay": pay_method, "balance": rem_bal_str
                        }
                        st.success(f"✅ 收件成功！已自動生成本次收據明細。")
                        st.rerun()

    if st.session_state.receipt_data:
        st.write("---")
        st.header("🖨️ 當天送洗單收據明細")
        r = st.session_state.receipt_data
        receipt_html = f"""
        <div style="background-color: #ffffff; color: #000000; padding: 20px; font-family: sans-serif; max-width: 350px; border: 1px solid #ccc; border-radius: 5px; margin-bottom: 10px;">
            <h3 style="text-align: center; margin: 0;">✨ 美舒容連鎖洗衣門市 ✨</h3>
            <p style="text-align: center; font-size: 12px; margin: 5px 0;">～ 收件入庫憑證 ～</p>
            <p>--------------------------------</p>
            <p style="margin: 5px 0;"><b>收件日期:</b> {r['date']}</p>
            <p style="margin: 5px 0;"><b>訂單單號:</b> {r['id']}</p>
            <p style="margin: 5px 0;"><b>顧客姓名:</b> {r['name']}</p>
            <p style="margin: 5px 0;"><b>行動電話:</b> {r['phone']}</p>
            <p>--------------------------------</p>
            <p style="margin: 5px 0;"><b>送洗品項:</b> {r['item']} x {r['qty']} 件</p>
            <p style="margin: 5px 0;"><b>花色/洗法:</b> {r['color']} ｜ {r['wash']}</p>
            <p style="margin: 5px 0;"><b>本次金額:</b> ${r['total']} 元</p>
            <p style="margin: 5px 0;"><b>付款方式:</b> {r['pay']}</p>
            <p>--------------------------------</p>
            <p style="margin: 5px 0; font-size: 16px;"><b>💰 帳戶客戶餘額: {r['balance']}</b></p>
            <p>--------------------------------</p>
            <p style="font-size: 11px; text-align: center; margin: 5px 0;">※ 請憑手機號碼於營業時間取件 ※</p>
        </div>
        """
        st.markdown(receipt_html, unsafe_allow_html=True)
        if st.button("關閉此收據顯示 / 接單下一位"):
            st.session_state.receipt_data = None
            st.rerun()

# =====================================================================
# TAB 2: 清洗進度看板 (進度追蹤變更)
# =====================================================================
with tab2:
    st.header("📋 門市衣物清洗狀態看版")
    if df_orders.empty:
