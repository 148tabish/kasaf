import streamlit as st  
import hackathon as callgpt  
from gptPrompt import system_prompt  
import json  
import os  
import re  
from datetime import datetime  
import requests  
  
def validate_input(question):  
    if not question:  
        return "Question cannot be empty"  
    if len(question) < 10:  
        return "Question is too short. Please provide more details."  
    return None  
  
def load_history():  
    if os.path.exists("history.json"):  
        with open("history.json", "r") as file:  
            return json.load(file)  
    return []  
  
def save_to_history(query, response):  
    history = load_history()  
    timestamp = datetime.now().strftime("%I:%M %d/%m/%Y ")  
    history.append({"query": query, "response": response, "timestamp": timestamp})  
    with open("history.json", "w") as file:  
        json.dump(history, file)  
  
def delete_history_item(index):  
    history = load_history()  
    if 0 <= index < len(history):  
        del history[index]  
    with open("history.json", "w") as file:  
        json.dump(history, file)  
  
def collect_feedback(query, response, feedback):  
    feedback_data = {"query": query, "response": response, "feedback": feedback}  
    with open("feedback.json", "a") as file:  
        json.dump(feedback_data, file)  
        file.write("\n")  
  
def load_solutions():  
    if os.path.exists("solutions.json"):  
        with open("solutions.json", "r") as file:  
            return json.load(file)  
    return []  
  
def save_solution(solution):  
    solutions = load_solutions()  
    solutions.append(solution)  
    with open("solutions.json", "w") as file:  
        json.dump(solutions, file)  
  
st.set_page_config(page_title='Hackathon Incident Management', page_icon='logo.png', layout='centered')  
  
# Custom CSS for consistent card size, spacing, and button alignment  
st.markdown("""  
    <style>  
    .card {  
        background-color: white;  
        border-radius: 10px;  
        padding: 20px;  
        margin: 10px;  
        height: 400px;  
        width: 365px;  
        display: flex;  
        flex-direction: column;  
        justify-content: space-between;  
        box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);  
        gap: 50px;  
    }  
    .card-content {  
        flex-grow: 1;  
        overflow-y: scroll;  
        height: 270px;  
    }  
    .card-content p {  
        margin: 0;  
        padding: 0;  
    }  
    .card-buttons {  
        display: flex;  
        justify-content: space-between;  
        margin-top: 10px;  
    }  
    .grid {  
        display: flex;  
        flex-wrap: wrap;  
    }  
    .stHorizontalBlock {  
        gap: 50px;  
    }  
    </style>  
    """, unsafe_allow_html=True)  
  
logo_path = "logo.png"  
st.image(logo_path, width=50)  
st.title("Incident Management Assistant")  
  
st.subheader("Ask your questions and get responses from MagnusGPT")  
st.markdown("###")  
  
st.sidebar.header("Query History")  
history = load_history()  
for idx, item in enumerate(history):  
    timestamp = item.get('timestamp', '')  
    with st.sidebar.expander(f"{item['query']} ({timestamp})"):  
        st.write(f"**Response:** {item['response']}")  
        if st.button("Delete", key=f"delete_{idx}"):  
            delete_history_item(idx)  
            st.rerun()  
  
if 'context' not in st.session_state:  
    st.session_state.context = []  
  
def process_query(query):  
    try:  
        full_context = "\n".join([f"User: {entry['user']}\nAssistant: {entry['assistant']}" for entry in st.session_state.context])  
        full_prompt = f"{system_prompt}\nUser: {query}\nAssistant:"  
        result = callgpt.callGPT(full_prompt)  
          
        if isinstance(result, dict) and "error" in result:  
            return result  
          
        response = result["choices"][0]["message"]["content"]  
        st.session_state.context.append({"user": query, "assistant": response})  
        return {"content": response}  
    except requests.exceptions.HTTPError as e:  
        if e.response.status_code == 429:  
            return {"error": "Too many requests. Please try again later."}  
        else:  
            return {"error": str(e)}  
    except ValueError as e:  
        return {"error": str(e)}  
  
def clean_response(response):  
    response = response.strip()  
    if response.startswith("```json"):  
        response = response[len("```json"):].strip()  
    if response.endswith("```"):  
        response = response[:-len("```")].strip()  
    # Remove problematic characters  
    response = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', response)  
    return response  
  
def display_response_in_grid_layout(response):  
    try:  
        cleaned_response = clean_response(response)  
        tickets = json.loads(cleaned_response)["tickets"]  
          
        num_columns = 3  # Number of columns in the grid  
        columns = st.columns(num_columns)  # Create columns  
          
        for i, ticket in enumerate(tickets):  
            col = columns[i % num_columns]  # Select the column for the current card  
            with col:  
                with st.container():  
                    st.markdown(f"""  
                    <div class="card">  
                        <div class="card-content">  
                            <h4>Incident No: {ticket['Incident No']}</h4>  
                            <p><strong>Short Description:</strong> {ticket['Short Description']}</p>  
                            <p><strong>Description:</strong> {ticket['Description']}</p>  
                        </div>  
                        <div class="card-buttons">  
                            <button id="like_{i}" onclick="document.getElementById('like_{i}').innerText='👍 Liked';">👍 Like</button>  
                            <button id="dislike_{i}" onclick="document.getElementById('dislike_{i}').innerText='👎 Disliked';">👎 Dislike</button>  
                        </div>  
                    </div>  
                    """, unsafe_allow_html=True)  
    except json.JSONDecodeError as e:  
        st.error(f"Failed to parse response (JSONDecodeError): {e}")  
    except KeyError as e:  
        st.error(f"Failed to parse response (KeyError): {e}")  
  
with st.form(key='query_form'):  
    prompt = st.text_input("Enter your question here", placeholder="Type your question...")  
    submit_button = st.form_submit_button(label='Submit')  
  
if submit_button:  
    validation_error = validate_input(prompt)  
    if validation_error:  
        st.error(validation_error)  
    else:  
        with st.spinner('Processing your request...'):  
            response = process_query(prompt)  
            print("👉👉👉👉👉")  # Debugging print to check raw response  
            print(response)  
            if "error" in response:  
                st.error(response["error"])  
            else:  
                st.markdown("###")  # Add some spacing  
                st.success("Query processed successfully!")  
                with st.container():  
                    st.markdown("**Question:**")  
                    st.write(prompt)  
                    st.markdown("**Response:**")  
                    display_response_in_grid_layout(response["content"])  
                  
                save_to_history(prompt, response["content"])  
  
if 'context' in st.session_state and st.session_state.context:  
    with st.form(key='followup_form'):  
        follow_up = st.text_input("Enter your follow-up question here", placeholder="Type your follow-up question...")  
        follow_up_submit_button = st.form_submit_button(label='Submit Follow-up')  
          
        if follow_up_submit_button and follow_up:  
            with st.spinner('Processing your follow-up request...'):  
                follow_up_response = process_query(follow_up)  
                if "error" in follow_up_response:  
                    st.error(follow_up_response["error"])  
                else:  
                    with st.container():  
                        st.markdown("**Follow-up Question:**")  
                        st.write(follow_up)  
                        st.markdown("**Response:**")  
                        display_response_in_grid_layout(follow_up_response["content"])  
  
# Solution submission form  
st.subheader("Submit Your Own Incident Solution")  
with st.expander("Submit a Solution"):  # This line makes the form collapsible  
    with st.form(key='solution_form'):  
        incident_no = st.text_input("Incident No")  
        short_description = st.text_input("Short Description")  
        solution_date = st.date_input("Date")  
        solution_time = st.time_input("Time")  
        solution_text = st.text_area("Your Solution")  
          
        solution_submit_button = st.form_submit_button(label='Submit Solution')  
      
    if solution_submit_button:  
        solution = {  
            "Incident No": incident_no,  
            "Short Description": short_description,  
            "Date": solution_date.strftime("%Y-%m-%d"),  
            "Time": solution_time.strftime("%H:%M:%S"),  
            "Solution": solution_text  
        }  
        save_solution(solution)  
        st.success("Solution submitted successfully!")  
  
# Display submitted solutions  
st.subheader("Submitted Solutions")  
solutions = load_solutions()  
if solutions:  
    for solution in solutions:  
        with st.expander(f"{solution['Incident No']} - {solution['Short Description']} ({solution['Date']} {solution['Time']})"):  
            st.write(solution["Solution"])  
  
st.markdown("---")  
st.markdown("Developed for the Hackathon event. ✅")  