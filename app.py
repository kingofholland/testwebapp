import os
from dotenv import load_dotenv
from time import sleep
from packaging import version
from flask import Flask, request, jsonify
import openai
import functions

# Check OpenAI version is correct
required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
load_dotenv()
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

if current_version < required_version:
    raise ValueError(f"Error: OpenAI version {openai.__version__} is less than the required version 1.1.1")
else:
    print("OpenAI version is compatible.")

# Start Flask app
app = Flask(__name__)

# Init client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Create an assistant or load an existing one
assistant_id = functions.create_assistant(client)

# Start conversation thread
@app.route('/start', methods=['GET'])
def start_conversation():
    print("Starting a new conversation...")
    thread = client.beta.threads.create()
    print(f"New thread created with ID: {thread.id}")
    return jsonify({"thread_id": thread.id})

# Generate response
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    thread_id = data.get('thread_id')
    user_input = data.get('message', '')

    if not thread_id:
        print("Error: Missing thread ID")
        return jsonify({"error": "missing thread_id"}), 400
    print(f"Received message: {user_input} for thread_id: {thread_id}")

    # Create a message in the thread
    client.beta.threads.messages.create(thread_id=thread_id, role="user", content=user_input)

    # Run the assistant
    run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)
    
    # Check if run requires action
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        print(f"Run status: {run_status.status}")
        if run_status.status == 'completed':
            break
        sleep(1)

    # Retrieve the latest message
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    response = messages.data[-1].content  # Adjust depending on the actual response structure
    print(f"Assistant response: {response}")
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)
