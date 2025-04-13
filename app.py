import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import google.generativeai as genai
from datetime import datetime


st.set_page_config(page_title="Personal Finance AI", layout="centered")

st.title("💰 Personal Finance AI Assistant")

# Load dataset
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("expenses.csv", parse_dates=["Date"])
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Date", "Category", "Amount", "Description"])
    return df

df = load_data()

# Add New Expense
st.subheader("➕ Add a New Expense")
with st.form("expense_form"):
    date = st.date_input("Date", value=datetime.today())
    category = st.selectbox("Category", ["Food", "Transport", "Groceries", "Entertainment", "Bills", "Other"])
    amount = st.number_input("Amount", min_value=1.0, step=1.0)
    desc = st.text_input("Description")
    submitted = st.form_submit_button("Add Expense")

    if submitted:
       new_data = pd.DataFrame([[date, category, amount, desc]], columns=df.columns)
       new_data["Date"] = pd.to_datetime(new_data["Date"])  # Convert to datetime
       df = pd.concat([df, new_data], ignore_index=True)
       df["Date"] = pd.to_datetime(df["Date"])  # Ensure all dates are datetime
       df.to_csv("expenses.csv", index=False)
       st.success("Expense added!")


# Show Data
st.subheader("📊 Your Expense History")
st.dataframe(df.sort_values(by="Date", ascending=False))

# Visualize Spending
st.subheader("📈 Spending by Category")
if not df.empty:
    category_sum = df.groupby("Category")["Amount"].sum().reset_index()
    fig, ax = plt.subplots()
    sns.barplot(data=category_sum, x="Category", y="Amount", ax=ax)
    ax.set_title("Total Spending by Category")
    st.pyplot(fig)

# Budget Analysis (basic)
st.subheader("💡 Insights")
if not df.empty:
    max_spend = df.groupby("Category")["Amount"].sum().idxmax()
    st.info(f"You spend the most on **{max_spend}**!")
else:
    st.warning("Add some expenses to see insights.")
# 💰 Budget Tracker
st.subheader("📅 Monthly Budget Tracker")

budget = st.number_input("Set your monthly budget (₹)", min_value=100.0, step=100.0)

if not df.empty:
    df["Date"] = pd.to_datetime(df["Date"])
    current_month = datetime.today().month
    monthly_spending = df[df["Date"].dt.month == current_month]["Amount"].sum()

    st.metric("Total Spending This Month", f"₹{monthly_spending:.2f}")

    if monthly_spending > budget:
        st.error(f"⚠️ You’ve exceeded your budget by ₹{monthly_spending - budget:.2f}")
    else:
        st.success(f"✅ You’re within your budget. ₹{budget - monthly_spending:.2f} remaining.")

    # 🤖 AI-Like Smart Suggestions
    st.subheader("🧠 Smart AI Suggestions")

    category_sum = df.groupby("Category")["Amount"].sum()
    max_cat = category_sum.idxmax()
    max_amt = category_sum.max()
    st.info(f"🧾 Your highest spending is on **{max_cat}** — ₹{max_amt:.2f}. Consider reviewing that.")

    last_week = datetime.today() - pd.Timedelta(days=7)
    recent_df = df[df["Date"] >= last_week]
    if not recent_df.empty:
        recent_sum = recent_df.groupby("Category")["Amount"].sum()
        if not recent_sum.empty:
            top_recent = recent_sum.idxmax()
            st.info(f"📅 In the past 7 days, you've spent most on **{top_recent}**. Budget accordingly.")

    low_spend = category_sum.idxmin()
    st.success(f"👍 You're doing well controlling your **{low_spend}** expenses!")

else:
    st.warning("Add more expenses to generate suggestions.")

# 🔐 Replace with your real Gemini API key
genai.configure(api_key="AIzaSyBNLeSzVoZJtke7QsjYgezSlOTgaDOuego")

def generate_financial_summary(df):
    month = datetime.today().strftime("%B")
    total = df["Amount"].sum()
    category_wise = df.groupby("Category")["Amount"].sum().to_dict()

    prompt = f"""
    You are a personal finance assistant.
    Summarize the user's spending for {month}.

    Total expenses: ₹{total:.2f}
    Spending by category: {category_wise}

    Offer clear insights and suggestions for improving money management next month.
    """

    try:
        model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
  # ✅ Use correct model name
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Gemini Error: {e}"



    # 🔍 Display AI-Powered Summary
st.subheader("🤖 AI-Powered Monthly Financial Summary")
with st.spinner("Analyzing your spending..."):
    try:
            summary = generate_financial_summary(df)
            st.success("Summary generated!")
            st.write(summary)
    except Exception as e:
            st.error(f"Failed to generate summary: {e}")

def chat_with_expense_bot(user_input, df):
    try:
        today = pd.Timestamp.today().normalize()
        df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()  # Normalize for comparison

        today_expense = df[df["Date"] == today]["Amount"].sum()
        total_expense = df["Amount"].sum()
        category_sum = df.groupby("Category")["Amount"].sum().to_dict()

        # Build context prompt
        prompt = f"""
        You are a personal finance assistant.
        The user has recorded expenses as a CSV file.

        Here’s some data to help:
        - Total spent today: ₹{today_expense:.2f}
        - Total expenses so far: ₹{total_expense:.2f}
        - Category-wise: {category_sum}

        Now answer this user question:
        {user_input}
        """

        model = genai.GenerativeModel("models/gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        return f"❌ Error in generating response: {e}"


