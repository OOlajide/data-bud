import os
from openai import OpenAI

# Initialize OpenAI client with the API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Function to generate SQL query considering multiple tables
def generate_sql_query(question: str, tables: dict) -> str:
    # Convert the tables and columns dictionary into a string for the prompt
    tables_description = ""
    for table_name, columns in tables.items():
        columns_description = "\n".join([f"- {col_name}: {col_desc}" for col_name, col_desc in columns.items()])
        tables_description += f"\nTable '{table_name}':\n{columns_description}\n"

    # Base names template query for reference
    base_names_template = '''
    SELECT
        BLOCK_NUMBER, -- the block number when the base name was registered
        BLOCK_TIMESTAMP, -- the block timestamp when the base name was registered
        TX_HASH, -- the unique transaction hash of the base name registration
        DECODED_LOG:owner::varchar, -- the address of the base name registrant
        DECODED_LOG:name::varchar -- the base name registered
    FROM base.core.fact_decoded_event_logs
    WHERE contract_address = lower('0x4cCb0BB02FCABA27e82a56646E81d8c5bC4119a5')
    AND event_name = 'NameRegistered'
    '''

    # Update the prompt to ensure AI only uses the provided tables and no unrelated inferences are made
    prompt = f'''
    Given the following question, generate an SQL query that answers it by selecting the appropriate table and columns from the available tables listed below.

    **Important**: Only use the tables listed below, do not infer or assume the existence of any other tables. If the question asks about a concept that doesn't have a matching table, respond that the required information is unavailable. For example, if the user asks about NFT mints and there is no table related to NFT mints, do not use the NFT sales table.

    If none of the tables directly correspond to the question, return a message stating that the data is not available in the provided tables.

    Question: {question}

    Available tables and their columns:
    {tables_description}

    Additionally, if the question involves 'base names,' use the following table and base query as a reference:
    {base_names_template}

    Generate a SQL query that answers the question. Make sure to use appropriate SQL syntax for Snowflake and only reference the columns mentioned above.
    Do not ever use quotes for column aliases, always use underscores for column aliases.

    Important: Do not use '*' in your SQL queries. Always specify the column names explicitly. For example, instead of 'SELECT COUNT(*)', use 'SELECT COUNT(column_name)'.

    Return only the SQL query, or if the necessary table does not exist, respond with 'The requested information is not available in the provided tables.'
    '''

    # Make the API call to OpenAI
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("OpenAI returned an empty response.")

    return content.strip()
