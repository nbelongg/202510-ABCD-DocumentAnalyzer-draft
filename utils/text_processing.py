"""Text processing utilities"""
from typing import List
import re


def break_into_paragraphs(text: str, max_length: int = 1000) -> str:
    """
    Break text into paragraphs for WhatsApp formatting
    
    WhatsApp has message limits, so this function adds double newlines
    after every paragraph to make messages more readable.
    
    Args:
        text: Input text
        max_length: Maximum length before forcing a break (default 1000 for WhatsApp)
        
    Returns:
        Formatted text with paragraph breaks
    """
    if not text:
        return ""
    
    # Split by existing double newlines first
    paragraphs = text.split('\n\n')
    
    result_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # If paragraph is too long, try to split it
        if len(para) > max_length:
            # Try to split by single newlines
            lines = para.split('\n')
            current = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if len(current) + len(line) + 1 > max_length:
                    if current:
                        result_paragraphs.append(current)
                    current = line
                else:
                    if current:
                        current += '\n' + line
                    else:
                        current = line
            
            if current:
                result_paragraphs.append(current)
        else:
            result_paragraphs.append(para)
    
    # Join with double newlines for clear separation
    return '\n\n'.join(result_paragraphs)


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove multiple spaces
    text = re.sub(r' +', ' ', text)
    
    # Remove multiple newlines (more than 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_sentences(text: str, max_sentences: int = 5) -> List[str]:
    """
    Extract first N sentences from text
    
    Args:
        text: Input text
        max_sentences: Maximum number of sentences
        
    Returns:
        List of sentences
    """
    if not text:
        return []
    
    # Simple sentence splitting (can be improved with NLTK)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences[:max_sentences]


def count_tokens_approximate(text: str) -> int:
    """
    Approximate token count (rough estimate)
    
    For more accurate counting, use tiktoken library
    
    Args:
        text: Input text
        
    Returns:
        Approximate token count
    """
    if not text:
        return 0
    
    # Rough approximation: 1 token ≈ 4 characters or 0.75 words
    # This is just an estimate
    words = text.split()
    return int(len(words) * 1.3)


def build_conversation_string(messages: List[dict], max_messages: int = 10) -> str:
    """
    Build conversation string from message history
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        max_messages: Maximum number of messages to include
        
    Returns:
        Formatted conversation string
    """
    if not messages:
        return ""
    
    # Take last N messages
    recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
    
    conversation_parts = []
    for msg in recent_messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        
        if role == 'user':
            conversation_parts.append(f"User: {content}")
        elif role == 'assistant':
            conversation_parts.append(f"Assistant: {content}")
    
    return '\n\n'.join(conversation_parts)


def format_context_for_prompt(contexts: List[dict]) -> str:
    """
    Format context information for LLM prompt
    
    Args:
        contexts: List of context dicts with 'pdf_context' and 'pdf_name'
        
    Returns:
        Formatted context string
    """
    if not contexts:
        return ""
    
    context_parts = []
    for i, ctx in enumerate(contexts, 1):
        pdf_name = ctx.get('pdf_name', f'Source {i}')
        pdf_context = ctx.get('pdf_context', '')
        
        context_parts.append(f"[Source {i}: {pdf_name}]\n{pdf_context}")
    
    return '\n\n---\n\n'.join(context_parts)

