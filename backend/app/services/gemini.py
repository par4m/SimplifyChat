import google.generativeai as genai
from ..core.config import settings
from ..schemas.chat import Message

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-latest')

async def generate_summary(messages: list[Message], participants: list[str]) -> dict:
    # Create the conversation text
    conversation_text = "\n".join([f"{msg.sender}: {msg.content}" for msg in messages])
    
    prompt = f"""Analyze this conversation between {', '.join(participants)}:

{conversation_text}

Provide:
1. A concise 3-sentence summary of the conversation
2. Key discussion points (as a list)
3. Action items (if any, as a list)"""
    
    response = await model.generate_content_async(prompt)
    content = response.text
    
    # Parse the response into structured format
    sections = content.split('\n\n')
    summary = sections[0].strip()
    key_points = [point.strip('- ') for point in sections[1].split('\n')[1:] if point.strip()]
    action_items = [item.strip('- ') for item in sections[2].split('\n')[1:] if item.strip()]
    
    return {
        "summary": summary,
        "key_points": key_points,
        "action_items": action_items
    } 