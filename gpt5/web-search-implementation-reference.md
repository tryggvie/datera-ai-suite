# Web Search Implementation Reference

This file contains the correct implementation patterns for using OpenAI's web search tool with the Responses API.

## ✅ Correct API Format

### Direct OpenAI Responses API Call
```bash
curl "https://api.openai.com/v1/responses" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_OPENAI_API_KEY" \
  -d '{
    "model": "gpt-5",
    "tools": [{"type": "web_search"}],
    "input": "What are the latest news about AI developments today?"
  }'
```

### Python Implementation
```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5",
    tools=[{"type": "web_search"}],
    input="What are the latest news about AI developments today?"
)

print(response.output_text)
```

### JavaScript Implementation
```javascript
import OpenAI from "openai";

const client = new OpenAI();

const response = await client.responses.create({
    model: "gpt-5",
    tools: [{ type: "web_search" }],
    input: "What are the latest news about AI developments today?"
});

console.log(response.output_text);
```

## ❌ Common Mistakes to Avoid

### Wrong: Using Chat Completions API
```python
# DON'T DO THIS - Chat Completions doesn't support web search
response = client.chat.completions.create(
    model="gpt-5",
    messages=[{"role": "user", "content": "What's the latest AI news?"}]
)
```

### Wrong: Missing tools parameter
```python
# DON'T DO THIS - Missing tools parameter
response = client.responses.create(
    model="gpt-5",
    input="What's the latest AI news?"
)
```

### Wrong: Incorrect tool type
```python
# DON'T DO THIS - Wrong tool type
response = client.responses.create(
    model="gpt-5",
    tools=[{"type": "web_search_preview"}],  # Wrong!
    input="What's the latest AI news?"
)
```

## 🔧 Our Backend Implementation

Our FastAPI backend correctly implements this by:

1. **Receiving requests** in our format:
   ```json
   {
     "messages": [{"role": "user", "content": "..."}],
     "model": "gpt-5",
     "verbosity": "medium",
     "reasoning_effort": "medium"
   }
   ```

2. **Converting to OpenAI format**:
   ```python
   response_params = {
       "model": request.model,  # gpt-5
       "input": input_data,     # Converted from messages
       "tools": [{"type": "web_search"}],  # ✅ Correct!
       "text": {
           "verbosity": request.verbosity
       },
       "reasoning": {
           "effort": request.reasoning_effort
       }
   }
   ```

3. **Calling OpenAI Responses API**:
   ```python
   response = client.responses.create(**response_params)
   ```

## 🧪 Testing Web Search

### Test if web search is working:
Look for these indicators in the response:
- Multiple `web_search_call` entries in the output
- `"type": "web_search_call"` with `"status": "completed"`
- Real-time information with proper citations
- URLs in the response text

### Example successful response structure:
```json
{
  "output": [
    {
      "type": "web_search_call",
      "status": "completed",
      "action": {
        "type": "search",
        "query": "AI news September 4, 2025"
      }
    },
    {
      "type": "message",
      "content": [
        {
          "type": "output_text",
          "text": "Here are the latest AI developments...",
          "annotations": [
            {
              "type": "url_citation",
              "url": "https://example.com/news"
            }
          ]
        }
      ]
    }
  ]
}
```

## 📝 Key Points

1. **Always use `tools: [{"type": "web_search"}]`** - not "web_search_preview"
2. **Use Responses API** - not Chat Completions API
3. **GPT-5 supports web search** - confirmed working as of 2025
4. **Fallback strategy**: Try GPT-5 first, then GPT-4o if needed
5. **Our backend handles the conversion** from our API format to OpenAI format

## 🔍 Debugging

If web search isn't working:
1. Check the API key is valid
2. Verify you're using the Responses API endpoint (`/v1/responses`)
3. Ensure `tools` parameter is included
4. Check the model supports web search (GPT-5, GPT-4o)
5. Look at the response for `web_search_call` entries

---
*Last updated: September 4, 2025*
*Tested with: GPT-5, OpenAI Responses API*
