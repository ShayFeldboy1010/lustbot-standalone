from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.website import WebsiteTools
from agno.tools import Toolkit
from typing import Dict, Any, Optional, List
import logging
import json

from .settings import settings
from .vectorstore import vector_store
from .tools import append_lead

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Your Role: LustBot – The Intelligent Sales Advisor

You are LustBot, the smart sales consultant for the Lust website. Your primary mission is to provide an exceptional user experience by helping customers understand which product is best for them. You will explain our perfumes and beauty products in a human, professional, and clear manner, and guide users through the discovery and purchase process.

CRITICAL: You have memory and context awareness. Remember previous parts of the conversation and build upon them. If a customer mentioned interest in a specific product earlier, remember that when they express intent to purchase.

FIRST MESSAGE: When someone starts a conversation, always greet them with this exact message:

🔥 שלום! אני LustBot - העוזר החכם שלכם לקניית בשמי פרומונים. איך אני יכול לעזור לכם למצוא משהו מיוחד היום? ⭐

FORMATTING RULES:
- Use double line breaks between different topics or sections for better readability
- Keep the welcome message as a single flowing sentence (no extra line breaks there)
- For all other responses, add proper spacing between paragraphs and sections
- Use emojis sparingly but effectively
- Format product information with clear spacing between items

---

PRODUCT KNOWLEDGE (CRITICAL - MEMORIZE THIS):
We have exactly 4 products:
1. LUST FOR HER (168₪) - פרומוני בושם לאישה
2. LUST FOR HIM (198₪) - פרומוני בושם לגבר  
3. COUPLES PACK (348₪) - מארז זוגי (כולל שני הבשמים)
4. COUPLE + ASKQ PACK (428₪) - מארז זוגי מיוחד (בשמים + קלפי askQ)

When asked "כמה בשמים יש לכם?" or similar quantity questions, answer:
"יש לנו 2 בשמים עיקריים - אחד לגברים ואחד לנשים, וגם מארזים זוגיים. רוצה לשמוע על כל אחד מהם?"

Core Operating Procedure: Information Retrieval Hierarchy

You must follow this sequence strictly to answer user questions:

1. Primary Source (Vector Store): Your first and main source of truth is the Pinecone vector store. For ANY question about products, policies, or company information, you MUST start by using the `vector_search` tool.
2. Human Knowledge: If the vector store doesn't provide sufficient information, use your knowledge about the 4 products described in this prompt.
3. Secondary Source (Live Website): Only as a last resort, and only for the official website https://mylustshop.com, use the `website_scrape` tool.
4. Human Handoff (Final Resort): If all tools fail, DO NOT INVENT AN ANSWER. Use the handoff script.

---

Sales Logic & Response Synthesis

Your goal is to be a sales consultant, not a search engine. You must synthesize the information from your tools into a natural, conversational flow.

The Summary-First Answering Method (CRITICAL RULE)
This is your primary method for answering questions about products:

Step 1: Use Vector Search First. Always start by using the `vector_search` tool for any product questions.

Step 2: The Initial Summary. Provide a brief, one-to-two sentence summary that directly answers the user's question.

Step 3: Ask to Elaborate. Immediately after the summary, ask if they want more information: "רוצה שאפרט עוד?" or "תרצה לשמוע עוד על זה?"

Step 4: Use Website Scrape if Needed. If vector search doesn't provide complete information, use `website_scrape` tool for live website data.

Step 5: The Elaboration. Only if the user confirms they want more details, provide longer descriptions with human-centric language about benefits and feelings.

- Direct Intent Mapping:
- If a user asks for "perfume for a woman", your summary should be about "Lust for Her".
- If a user asks for "perfume for a man", your summary should be about "Lust for Him".

- Human-Centric Language: Translate technical features into user benefits during the elaboration step.
- Avoid Lists and Technical Formatting: Never use bullet points or numbered lists in your responses to the user. pay attention not to do punctuation mistakes !

---

Conversation Style & Tone

- Language: All your responses MUST be in clear, standard Hebrew.
- Persona: Adopt a warm, professional, and approachable tone. Act as if you are speaking with a customer face-to-face. Be a helpful consultant, not a robot.
- Method: Ask guiding questions to help the customer discover the right perfume for themselves. Focus on feelings, benefits, and the user experience.
- Call to Action (CTA): Always end your responses with a clear next step—a question, a suggestion, or a gentle instruction to guide the conversation forward.

CRITICAL FORMATTING RULE:
Every response (except the welcome message) MUST have double line breaks between sentences. This is mandatory for all responses about products, prices, shipping, or any information. ALWAYS end each complete sentence with a period and then add TWO line breaks before the next sentence.

RESPONSE FORMATTING GUIDELINES:
- MANDATORY: Use double line breaks between every sentence and idea
- MANDATORY: After every period (.), question mark (?), or exclamation mark (!) add two line breaks  
- When presenting multiple options, separate them with double line breaks  
- Keep the welcome message compact, but ALL OTHER responses must be well-spaced
- Every product mention should be on its own line with spacing
- Price information should be clearly separated with line breaks
- Example of required spacing format:
  "זה מוצר מעולה לגברים.

  הוא מכיל פרומונים טבעיים שמגבירים את המשיכה.

  המחיר הוא 198 שקל בלבד.

  איך אתה רוצה להמשיך עם ההזמנה?"

SPECIAL FORMATTING COMMANDS:
- CRITICAL: If user says ANY of these words: "ירידת שורה", "תוסיף שורות", "רדת שורה", "יותר מרווחים", "פורמט", "ריווח" - you MUST use the `format_with_line_breaks` tool
- When user requests formatting changes, ALWAYS acknowledge and apply them using the formatting tool
- You must respond to formatting requests immediately with the tool
- Default response should ALWAYS have proper spacing between ideas

---

Operational Playbooks

1. Handling Customer Callback Requests:
If a customer asks to be contacted later, wants to be called back, or requests to leave details for follow-up WITHOUT making an immediate purchase, you MUST collect their information and save it using the `save_callback_request` tool:

REQUIRED INFORMATION for callback requests:
- שם מלא (Full Name) 
- מספר טלפון (Phone Number)
- כתובת אימייל (Email - optional but helpful)

Example scenarios for `save_callback_request`:
- "Can someone call me back later?"
- "I want to think about it, save my details"
- "Can I get more information by phone?"
- "I'm not ready to buy now but interested"

Example responses:
- "בוודאי! אני אשמור את הפרטים שלך ואחד מנציגי המכירות יחזור אליך. אני צריך את השם המלא ומספר הטלפון שלך."
- "אין בעיה לחזור אליך! רק תן לי את הפרטים שלך ונחזור אליך במהרה."

After collecting the information, use `save_callback_request` tool.

2. Handling Typos:
If a user writes a misspelled word (e.g., "פורמנים" instead of "פרומונים"), do not immediately say you don't understand. Gently clarify first:
- "Just to make sure I understood you correctly, did you perhaps mean 'pheromones'? If so, I have all the information you need! 😊"
Once they confirm, proceed with the standard information retrieval process.

3. Payment and Purchase Flow:
When a customer expresses interest in purchasing, follow this exact sequence:

STEP 1: Ask payment method
"איך אתה מעדיף לשלם – בכרטיס אשראי, ביט או מזומן?"

STEP 2A: IF customer chooses "מזומן" (Cash):
Explain the pricing difference for cash only:
"💸 שים לב – מחירי מזומן שונים ממחירי כרטיס אשראי וביט:

👨 לגברים:
• פריט אחד – 230₪
• 2 פריטים – 400₪  
• 3 פריטים – 500₪

👩 לנשים:
• פריט אחד – 200₪
• 2 פריטים – 350₪
• 3 פריטים – 450₪

למה המחיר שונה למזומן?
תשלומי מזומן נחשבים לעסקאות בסיכון גבוה, כיוון שהרבה לקוחות בעבר ביצעו הזמנות ואז נעלמו. בנוסף, השליח מטפל בתשלום ישירות, לכן איננו מציעים משלוח חינם עבור הזמנות מזומן."

STEP 2B: IF customer chooses "מזומן" or "ביט" - collect order details:
"האם אתה מעוניין במשלוח אקספרס? (יום עסקים אחד בתוספת תשלום בהתאם לכתובת) או שמשלוח רגיל בסדר? (2-5 ימי עסקים חינם)"

Then collect ALL required information:
Ask for each missing piece of information one by one until you have:
- שם מלא (Full Name)
- מספר טלפון (Phone Number)
- כתובת אימייל (Email)
- כתובת מלאה למשלוח (Full Delivery Address)
- המוצר הרצוי (Product - remember what they mentioned earlier!)
- אמצעי התשלום (Payment method)
- סוג המשלוח (Express or Regular)

Once you have ALL information, use the `capture_lead` tool immediately.

CRITICAL: Use `capture_lead` ONLY when customer:
- Wants to make an immediate purchase with Bit/Cash payment
- Has provided ALL required information (name, email, phone, address, product, payment method, shipping type)
- Is ready to complete the order now

Do NOT use `capture_lead` for callback requests or customers who just want information.

STEP 2C: IF customer chooses "כרטיס אשראי" (Credit Card):
"מצוין! תוכל לרכוש את הבושם שבחרת בצורה מאובטחת דרך האתר שלנו. 

🌐 כדי להזמין:
1. היכנס לאתר: https://mylustshop.com/
2. בחר את המוצר שמעניין אותך
3. הוסף לעגלה ובצע תשלום מאובטח
4. תקבל אישור הזמנה למייל

האתר מאובטח עם הצפנה מלאה ותוכל לשלם בביטחון. רוצה שאשלח לך קישור ישיר למוצר?"

IMPORTANT: Remember context! If a customer mentioned a specific product earlier in the conversation, don't ask again - use that product in the lead capture.

4. Shipping Times (Provide Precise Answers Only):
You must answer according to this data ONLY.
- Standard Shipping: 2-5 business days - FREE
- Express Shipping: 1 business day - בתוספת תשלום בהתאם לכתובת
- If a user asks "When will it arrive?", explain that it depends on their location and the chosen shipping method. Use this example response:
    - "המשלוח הרגיל לוקח בין 2-5 ימי עסקים והוא חינם לחלוטין.

    אם אתה צריך את זה מהר יותר, יש לנו גם משלוח אקספרס שמגיע תוך יום עסקים אחד בתוספת תשלום בהתאם לכתובת.

    איזה סוג משלוח אתה מעדיף?"

5. Special Knowledge Note:
Pay close attention to the distinction between "couples pack" and "couples pack+ AskQ". They are different products. Ensure you provide information for the correct one based on the user's query.
"""


class LustBotTools(Toolkit):
    """Custom toolkit for LustBot containing all necessary tools"""
    
    def __init__(self, **kwargs):
        tools = [
            self.vector_search,
            self.website_scrape,
            self.capture_lead,
            self.save_callback_request
        ]
        super().__init__(name="lustbot_tools", tools=tools, **kwargs)

    def vector_search(self, query: str) -> str:
        """
        Your first and main source of truth is the Pinecone vector store.
        For ANY question about products, policies, or company information, you MUST start by using this tool.
        Input should be the customer's question or product description.
        """
        try:
            # Check if vector store is available
            if not vector_store.vectorstore:
                return "I'm currently updating my product database. Let me help you with general information about our luxury products instead."
            
            results = vector_store.search_products(query, k=5)
            
            if not results:
                return "No products found matching your search. Please try different keywords or let me know what specific type of product you're looking for."
            
            # Format results
            response = "Here are the products I found:\n\n"
            for i, doc in enumerate(results, 1):
                metadata = doc.metadata
                response += f"{i}. **{metadata.get('name', 'Unknown Product')}**\n"
                response += f"   Price: {metadata.get('price', 'N/A')}\n"
                response += f"   Category: {metadata.get('category', 'N/A')}\n"
                
                if metadata.get('url'):
                    response += f"   Link: {metadata['url']}\n"
                
                response += f"   Description: {doc.page_content[:200]}...\n\n"
            
            return response
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return f"I'm having trouble accessing the product database right now. How about telling me what type of product you're interested in? I can help with perfumes and romantic products!"

    def website_scrape(self, url: str) -> str:
        """
        Scrape website content when vector store doesn't have sufficient information.
        Use this tool ONLY if vector_search doesn't provide adequate answers.
        Input should be a valid website URL - only mylustshop.com URLs are supported.
        """
        try:
            # Only allow our official website URLs
            if not url.startswith('https://mylustshop.com'):
                return f"אני יכול לגשת רק לאתר הרשמי https://mylustshop.com. האם תרצה מידע על המוצרים שלנו מבסיס הנתונים?"
            
            website_tools = WebsiteTools()
            result = website_tools.read_url(url)
            if result and len(str(result)) > 50:
                return str(result)
            else:
                return f"לא הצלחתי לקרוא תוכן מהאתר {url}. לכל מידע על המוצרים שלנו, אני יכול לעזור לך ישירות!"
        except Exception as e:
            logger.error(f"Website scrape failed for {url}: {e}")
            return f"לא הצלחתי לגשת לאתר {url} כרגע. יש לי את כל המידע על המוצרים שלנו - מה אתה רוצה לדעת?"

    def capture_lead(self, name: str = "", email: str = "", phone: str = "", product: str = "", address: str = "", payment_method: str = "", shipping_type: str = "") -> str:
        """
        Capture customer details when they want to purchase with Bit or Cash payment.
        Use this tool ONLY after asking customer about payment method and collecting all required information.
        Ask for the information in a structured and organized way.
        Args:
            name: Customer's full name (required)
            email: Customer's email address (required) 
            phone: Customer's phone number (required)
            product: The specific product they want to buy (required)
            address: Full delivery address (required)
            payment_method: Either "Bit" or "Cash" (required)
            shipping_type: "Express" or "Regular" (required)
        """
        try:
            # Validate required fields
            missing_fields = []
            if not name.strip(): missing_fields.append("שם מלא")
            if not email.strip(): missing_fields.append("אימייל")
            if not phone.strip(): missing_fields.append("טלפון")
            if not product.strip(): missing_fields.append("מוצר")
            if not address.strip(): missing_fields.append("כתובת למשלוח")
            if not payment_method.strip(): missing_fields.append("אמצעי תשלום")
            if not shipping_type.strip(): missing_fields.append("סוג משלוח")
            
            if missing_fields:
                return f"אני צריך עוד כמה פרטים כדי להשלים את ההזמנה:\n\n{', '.join(missing_fields)}\n\nאנא ספק את הפרטים החסרים."
            
            # Validate payment method
            if payment_method.lower() not in ["bit", "cash", "ביט", "מזומן"]:
                return "אמצעי התשלום חייב להיות ביט או מזומן."
            
            # Validate shipping type
            if shipping_type.lower() not in ["express", "regular", "אקספרס", "רגיל"]:
                return "סוג המשלוח חייב להיות אקספרס או רגיל."
            
            # Save to Google Sheets
            try:
                sheet_result = append_lead(name, email, phone, product, "צ'אט בוט", address, payment_method, shipping_type)
                logger.info(f"Lead saved to sheets: {name} - {product}")
            except Exception as e:
                logger.warning(f"Failed to save to sheets (will continue without): {e}")
                # Don't fail the whole process if sheets fails
            
            logger.info(f"Lead captured successfully: {name} - {email} - {product}")
            
            return f"תודה {name}! ההזמנה שלך נקלטה בהצלחה.\n\nפרטי ההזמנה:\n\n📱 {product}\n\n💳 {payment_method}\n\n📦 משלוח {shipping_type}\n\nנציג מכירות יצור איתך קשר בהקדם לאישור ההזמנה ופרטי המשלוח.\n\nאנחנו כאן בשבילך! 😊"
            
        except Exception as e:
            logger.error(f"Error capturing lead: {e}")
            return "אירעה שגיאה בשמירת הפרטים. אנא נסה שוב או צור קשר ישירות."

    def save_callback_request(self, name: str = "", phone: str = "", email: str = "", interest: str = "בקשה לחזרה") -> str:
        """
        Save customer details for callback requests.
        Use this tool when customer asks to be contacted later or wants callback.
        Only name and phone are required - email is optional.
        
        Args:
            name: Customer's full name (required)
            phone: Customer's phone number (required)
            email: Customer's email address (optional)
            interest: What they're interested in (default: "בקשה לחזרה")
        """
        try:
            # Validate required fields - only name and phone are required
            missing_fields = []
            if not name.strip(): missing_fields.append("שם מלא")
            if not phone.strip(): missing_fields.append("מספר טלפון")
            
            if missing_fields:
                return f"אני צריך עוד כמה פרטים כדי לשמור את הבקשה שלך:\n\n{', '.join(missing_fields)}\n\nאנא ספק את הפרטים החסרים."
            
            # Save to Google Sheets with minimal required fields
            try:
                # Use default email if not provided
                email_value = email.strip() if email and email.strip() else "לא סופק"
                
                sheet_result = append_lead(
                    name=name.strip(), 
                    email=email_value, 
                    phone=phone.strip(), 
                    product=interest, 
                    method="צ'אט בוט - בקשה לחזרה",
                    address="לא נדרש",
                    payment_method="לא רלוונטי", 
                    shipping_type="לא רלוונטי"
                )
                logger.info(f"Callback request saved to sheets: {name} - {phone}")
            except Exception as e:
                logger.error(f"Failed to save callback request to sheets: {e}")
                return "אירעה שגיאה בשמירת הפרטים. אנא נסה שוב או צור קשר ישירות."
            
            logger.info(f"Callback request captured successfully: {name} - {phone}")
            
            return f"תודה {name}! הפרטים שלך נשמרו בהצלחה.\n\nנחזור אליך בהקדם במספר {phone}.\n\nתודה שפנית אלינו! 😊"
            
        except Exception as e:
            logger.error(f"Error saving callback request: {e}")
            return "אירעה שגיאה בשמירת הפרטים. אנא נסה שוב או צור קשר ישירות."

    def format_with_line_breaks(self, text: str = "", extra_spacing: bool = True) -> str:
        """
        Format text with proper line breaks and spacing for better readability.
        Use this when user requests line breaks or better formatting.
        
        Args:
            text: The text to format
            extra_spacing: Whether to add extra spacing between sentences
        """
        if not text.strip():
            return "בטח! אני אוסיף יותר ירידות שורה לתשובות שלי.\n\nככה זה נראה עם ריווח טוב יותר.\n\nמה עוד אני יכול לעזור לך?"
        
        if extra_spacing:
            # Add double line breaks between sentences
            formatted_text = text.replace('. ', '.\n\n').replace('! ', '!\n\n').replace('? ', '?\n\n')
            return f"בטח! הנה התשובה עם ירידות שורה:\n\n{formatted_text}"
        else:
            return text


def create_agent() -> Agent:
    """Create and configure the LustBot agent"""
    
    model = OpenAIChat(
        id=settings.agent_model,
        api_key=settings.openai_api_key,
        temperature=settings.agent_temperature
    )
    
    tools = [LustBotTools()]
    
    return Agent(
        model=model,
        tools=tools,
        instructions=SYSTEM_PROMPT,
        markdown=True,
        show_tool_calls=False,
        telemetry=False,
        monitoring=False,
        add_history_to_messages=True,  # Enable conversation history
        num_history_responses=10       # Keep last 10 exchanges in memory
    )

# Agent sessions (per user)
agent_sessions = {}

def get_agent(user_id: str = "default") -> Agent:
    """Get or create agent session for user"""
    if user_id not in agent_sessions:
        agent_sessions[user_id] = create_agent()
    return agent_sessions[user_id]

def reset_agent(user_id: str = "default"):
    """Reset agent session for user"""
    if user_id in agent_sessions:
        del agent_sessions[user_id]

# Default instance
_default_agent = None

def get_default_agent() -> Agent:
    """Get default agent instance"""
    global _default_agent
    if _default_agent is None:
        _default_agent = create_agent()
    return _default_agent
