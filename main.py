import streamlit as st
import pandas as pd
import plotly.express as px
import json
from openai_helper import generate_sql_query
from flipside_helper import execute_flipside_query

# Streamlit page config
st.set_page_config(page_title="Data Bud", layout="wide")

st.write('''<style>
[data-testid="stDataFrameResizable"] {
        border: 2px solid rgba(250, 250, 250, 0.1) !important;
}
</style>''', unsafe_allow_html=True)

# Initialize the session state variable if it doesn't exist
if "query_result" not in st.session_state:
    st.session_state.query_result = None

if "previous_question" not in st.session_state:
    st.session_state.previous_question = ""

# Define the schemas for multiple tables
contracts_schema = {
    "ADDRESS": "The address of the contract.",
    "CREATED_BLOCK_NUMBER": "The block number when the contract was created.",
    "CREATED_BLOCK_TIMESTAMP": "The block timestamp when the contract was created.",
    "CREATED_TX_HASH": "The transaction hash when the contract was created.",
    "CREATOR_ADDRESS": "The address of the creator of the contract."
}

transactions_schema = {
    "TX_HASH": "The unique identifier that is generated when a transaction is executed.",
    "BLOCK_NUMBER": "The block number when the transaction occurred.",
    "BLOCK_TIMESTAMP": "The block timestamp when the transaction occurred.",
    "FROM_ADDRESS": "The address that initiated the transaction.",
    "TO_ADDRESS": "The receiving address of the transaction. This can be a contract address.",
    "TX_FEE": "Fee paid in ETH to validate the transaction.",
    "STATUS": "Status of the transaction, 'SUCCESS' for a successful transaction or 'FAIL' for a failed transaction"
}

token_transfers_schema = {
    "BLOCK_NUMBER": "The block number when the token transfer occurred.",
    "BLOCK_TIMESTAMP": "The block timestamp when the token transfer occurred.",
    "TX_HASH": "The unique identifier that is generated when a token is transferred.",
    "CONTRACT_ADDRESS": "The contract address of the token being transferred.",
    "FROM_ADDRESS": "The address that sent the token.",
    "TO_ADDRESS": "The address receiving the token.",
    "AMOUNT": "The amount of tokens transferred.",
    "AMOUNT_USD": "The value of the tokens transferred in USD.",
    "SYMBOL": "The symbol of the token being transferred."
}

dex_swaps_schema = {
    "BLOCK_NUMBER": "The block number when the swap occurred.",
    "BLOCK_TIMESTAMP": "The block timestamp when the swap occurred.",
    "TX_HASH": "The unique identifier that is generated when the swap is executed.",
    "ORIGIN_FROM_ADDRESS": "The address that initiated the swap.",
    "POOL_NAME": "The name of the liquidity pool involved in the swap.",
    "AMOUNT_IN": "The amount of tokens being swapped in.",
    "AMOUNT_IN_USD": "The USD value of the tokens swapped in.",
    "AMOUNT_OUT": "The amount of tokens received in the swap.",
    "AMOUNT_OUT_USD": "The USD value of the tokens swapped out.",
    "TX_TO": "The address receiving the tokens after the transaction.",
    "PLATFORM": "The DEX platform on which the swap took place.",
    "TOKEN_IN": "The address of the token sent for swap.",
    "TOKEN_OUT": "The address of the token being being swapped to.",
    "SYMBOL_IN": "The symbol of the token sent for swap.",
    "SYMBOL_OUT": "The symbol of the token being swapped to."
}

nft_sales_schema = {
    "BLOCK_NUMBER": "The block number when the NFT sale occurred.",
    "BLOCK_TIMESTAMP": "The block timestamp when the NFT sale occurred.",
    "TX_HASH": "The unique identifier for the NFT sale transaction.",
    "PLATFORM_NAME": "The name of the NFT marketplace where the NFT sale took place.",
    "SELLER_ADDRESS": "The address of the NFT seller.",
    "BUYER_ADDRESS": "The address of the NFT buyer.",
    "NFT_ADDRESS": "The contract address of the NFT sold.",
    "PROJECT_NAME": "The name of the NFT sold.",
    "PRICE_USD": "The USD value of the NFT sale."
}

# Custom schema for base names
custom_base_names_schema = {
    "BLOCK_NUMBER": "The block number when the base name was registered.",
    "BLOCK_TIMESTAMP": "The block timestamp when the base name was registered.",
    "TX_HASH": "The unique transaction hash of the base name registration.",
    "DECODED_LOG:owner::varchar": "The address of the base name registrant.",
    "DECODED_LOG:name::varchar": "The base name registered."
}

# Dictionary to hold all available tables and their columns
tables = {
    "base.core.dim_contracts": contracts_schema,
    "base.core.fact_transactions": transactions_schema,
    "base.core.ez_token_transfers": token_transfers_schema,
    "base.defi.ez_dex_swaps": dex_swaps_schema,
    "base.nft.ez_nft_sales": nft_sales_schema
}

st.title("Data Bud")

st.write('Explore [Base](https://base.org) on-chain data with natural language')

# User input for the question
user_question = st.text_input(label="Enter your question:", placeholder="How many base names were registered daily in the last 14 days?")

# Check if the question has changed
if user_question != st.session_state.previous_question:
    st.session_state.query_result = None  # Reset query result
    st.session_state.previous_question = user_question  # Update the previous question

if user_question and st.session_state.query_result is None:
    try:
        with st.spinner('Generating query, please wait...'):
            # Generate SQL query using OpenAI
            sql_query = generate_sql_query(user_question, tables)  # Pass the tables schema here

        st.subheader("Generated SQL Query:")
        st.code(sql_query, language="sql")
        with st.spinner('Running query, please wait...'):
            # Execute the query using Flipside API
            result = execute_flipside_query(sql_query)
            st.session_state.query_result = result  # Store the result in session_state

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# Retrieve the stored query result
result = st.session_state.query_result

if result is not None:
    st.subheader("Query Results:")
    if isinstance(result, pd.DataFrame):
        # Remove '__row_index' column if it exists
        if '__row_index' in result.columns:
            result = result.drop(columns=['__row_index'])
        st.dataframe(result, width=1000)

        # Chart builder
        st.subheader("Build a Chart")

        # Chart type selection
        chart_type = st.selectbox("Select chart type:", ["Pie", "Line", "Bar", "Area"])

        if chart_type == "Pie":
            size_col = st.selectbox("Select Size column:", [None] + list(result.columns), index=0)
            value_col = st.selectbox("Select Value column:", [None] + list(result.columns), index=0)

            # Ensure both columns are selected before creating the pie chart
            if size_col and value_col:
                fig = px.pie(result, names=size_col, values=value_col)
                st.plotly_chart(fig)
            else:
                st.warning("Please select both size and value columns to generate the Pie chart.")

        else:
            x_col = st.selectbox("Select X axis:", [None] + list(result.columns), index=0)
            y_col = st.selectbox("Select Y axis:", [None] + list(result.columns), index=0)

            # Ensure both x_col and y_col are selected before creating the chart
            if x_col and y_col:
                if chart_type == "Line":
                    fig = px.line(result, x=x_col, y=y_col)
                elif chart_type == "Bar":
                    fig = px.bar(result, x=x_col, y=y_col)
                elif chart_type == "Area":
                    fig = px.area(result, x=x_col, y=y_col)

                st.plotly_chart(fig)
            else:
                st.warning("Please select both X and Y columns to generate the chart.")

st.subheader("Question Tips")
with st.expander("Click to view tips for writing questions"):
    st.write("""
        Here are some tips to get the best results when asking questions:

        - **Specify time frames**: Including a time frame (e.g., "in the last 7 days" or "between January and February 2023") will narrow down the results and make queries faster.
        - **Be clear and concise**: Clearly specify what you're looking for in a question to avoid ambiguity.
        - **Longer timeframes may take longer**: Queries involving longer periods could take more time to process, so expect a slight delay.
        - **Ask about specific actions**: For example, "Show the daily number of swaps on Platform X" or "How much USD value of tokens was swapped in the last month?"

        #### Sample Questions:

        - How many base names were registered in the last 14 days?
        - Who registered the most base names this month?
        - What were the base names registered on a specific date (e.g., October 10, 2024)?

        - Show the top 5 contract creators by the number of contracts created.
        - How many successful transactions were executed yesterday?
        - What is the total transaction fee in the last week?
        - What was the total amount of USD transferred in token transfers over the last 30 days?
        - Which token was transferred the most in the past month?
        - Show the daily total USD value of tokens swapped in the last 7 days.
        - Which token pairs had the highest swap volume in the last week?
        - How many NFTs were sold in the last 30 days?
    """)

st.subheader("Table Schemas")
with st.expander("Click to view Data Bud table schemas in JSON format"):
    # Combine the tables and custom schema
    combined_schemas = {**tables, "custom_base_names_query": custom_base_names_schema}
    st.json(combined_schemas)