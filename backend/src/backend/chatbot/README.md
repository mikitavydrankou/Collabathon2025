# Chatbot System for Neurodivergent Users

A simple, user-friendly chatbot system for assisting with money transfers. Designed specifically for neurodivergent users with clear, step-by-step interactions.

## Architecture

### Three LLM-Powered Agents

All agents use **LangChain with OpenAI** (gpt-4o-mini) for intelligent decision-making.

1. **Suggestion Agent** (`agents.py:SuggestionAgent`)
   - Uses LLM to analyze transaction history
   - Picks the best suggestion from first suggestions based on temporal patterns, recurring bills, and user needs
   - Uses LLM to format filter suggestions with intelligent confidence scoring (only suggests if 90%+ confident)
   - **Why LLM?** Better understanding of payment patterns (e.g., "electricity bill from month ago = likely recurring")

2. **Suggestion Verifier Agent** (`agents.py:SuggestionVerifierAgent`)
   - Called during field collection (after collecting 2+ fields)
   - Filters past transactions based on partial input
   - Uses LLM to match partial user input with past transactions
   - Only suggests if confidence >= 90%
   - **Why LLM?** Can fuzzy-match partial names/amounts better than rules

3. **Main Agent** (`agents.py:MainAgent`)
   - Collects 4 fields one by one:
     1. Recipient account number (basic validation)
     2. Recipient full name (LLM validates and formats properly)
     3. Amount to transfer (LLM parses various formats: "100 zł", "100.50", "100 pln")
     4. Transaction description
   - Uses LLM to explain validation problems in simple, neurodivergent-friendly language
   - Runs final check using MCP `final_check_tool`
   - **Why LLM?** Better parsing of varied input formats, clearer error messages

### Workflow

```
START
  |
  v
[Initial Stage] - "Want a suggestion?"
  |
  +-- YES --> [First Suggestion Stage]
  |             |
  |             +-- ACCEPT --> [Completed] --> Payment Page
  |             |
  |             +-- DECLINE --> [Collecting Fields]
  |
  +-- NO --> [Collecting Fields]
               |
               v
            [Field 1: Account Number]
               |
               v
            [Field 2: Full Name]
               |
               v  (Check for filter suggestion if 2+ fields & not shown yet)
            [Filter Suggestion?]
               |
               +-- YES (confidence >= 90%) --> [Filter Suggestion Stage]
               |                                  |
               |                                  +-- ACCEPT --> [Completed]
               |                                  |
               |                                  +-- DECLINE --> Continue
               |
               v
            [Field 3: Amount]
               |
               v
            [Field 4: Description]
               |
               v
            [Final Check] - Call final_check_tool
               |
               +-- No problems --> [Completed] --> Payment Page
               |
               +-- Has problems --> [Final Check Stage] - Ask user
                                       |
                                       +-- CONTINUE --> [Completed]
                                       |
                                       +-- CANCEL --> [Initial Stage]
```

## API Endpoints

### POST `/chatbot/start`
Start a new chatbot session.

**Request:**
```json
{
  "user_id": 1
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "message": "Hi! I can help you make a payment...",
  "buttons": ["yes", "no"]
}
```

### POST `/chatbot/message`
Send a message or action to the chatbot.

**Request:**
```json
{
  "session_id": "uuid",
  "user_id": 1,
  "message": "John Doe",  // Optional: text message
  "action": "yes"         // Optional: button action
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "stage": "collecting_field_2",
  "message": "Got it!\n\nPlease enter the amount to transfer.",
  "buttons": null,
  "suggestion": null,
  "transaction_data": {
    "recipient_account": "DE12345678901234567890",
    "recipient_name": "John Doe",
    "amount": null,
    "transaction_text": null
  },
  "show_confirm_payment": false,
  "validation_problems": null
}
```

### GET `/chatbot/session/{session_id}`
Get current session state.

## MCP Tools Integration

The chatbot uses three MCP server tools via HTTP API on port 8001:

1. **POST /tools/first-suggestion** - Get up to 5 transactions with temporal context
2. **POST /tools/filter-suggestion** - Filter transactions by partial input
3. **POST /tools/final-check** - Validate complete transaction data

The `mcp_client.py` uses `httpx` to make HTTP requests to the MCP server instead of direct code imports.

## Session Management

Sessions are stored in-memory using a dictionary (`ChatbotService.sessions`).

**For production:** Use Redis or database for session persistence.

## State Machine

The chatbot uses a state machine with these stages:

- `INITIAL` - Want suggestion?
- `FIRST_SUGGESTION` - Showing first suggestion
- `COLLECTING_FIELD_1` - Collecting recipient account
- `COLLECTING_FIELD_2` - Collecting full name
- `COLLECTING_FIELD_3` - Collecting amount
- `COLLECTING_FIELD_4` - Collecting transaction text
- `FILTER_SUGGESTION` - Showing filter suggestion
- `FINAL_CHECK` - Validation problems
- `COMPLETED` - Ready for payment

## Design Principles for Neurodivergent Users

1. **One thing at a time** - Collect one field per message
2. **Clear language** - Simple, direct prompts
3. **Visual feedback** - Buttons for common actions
4. **Validation** - Immediate feedback on input
5. **Helpful suggestions** - But never forced
6. **Confirm before action** - Always show what will happen

## Environment Setup

**Required Environment Variables:**

In `.env` file:
```env
# Database
DATABASE_NAME=your_database_name
DATABASE_USERNAME=your_username
DATABASE_PASSWORD=your_password

# MCP Server
MCP_SERVER_URL=http://localhost:8001

# OpenAI API Key (required for LLM agents)
OPENAI_API_KEY=your_openai_api_key_here
```

## Testing

To test the chatbot:

1. **Set OpenAI API Key** in `.env`
2. Start the MCP server: `cd mcp_server && poetry run start` (runs on port 8001)
3. Start the backend: `cd backend && poetry run dev` (runs on port 8000)
4. Start the frontend: `cd frontend && npm run dev` (runs on port 3000)
5. Login to the app at http://localhost:3000
6. Click "Payment Helper" button
7. Follow the chatbot prompts

**Important:**
- Make sure the MCP server is running on port 8001 before starting the backend!
- OpenAI API key must be set for LLM agents to work

## Future Improvements

- [ ] Persist sessions to Redis/database
- [ ] Add support for editing previous fields
- [ ] Voice input support
- [ ] More sophisticated NLP for understanding freeform input
- [ ] A/B testing different prompt styles
- [ ] Analytics on user completion rates
