import re
import os
import unicodedata
import platform
import subprocess

import tiktoken
from .constants import TOKENIZER

def get_encoding(model: str = None):
    try:
        if model:
            return tiktoken.encoding_for_model(model)
        return tiktoken.get_encoding(TOKENIZER[0])
    except KeyError:
        return tiktoken.get_encoding(TOKENIZER[0])


def number_of_tokens(messages: str | list[str], model: str = TOKENIZER[0]):
    """
    Returns the number of tokens used by a list of messages.

    Parameters
    ----------
    messages : str or list of str
        A single message or a list of messages to be processed. Each message
        can be a string.
    model : str, optional
        The name of the model used for token encoding (default is MODELS[0]).

    Returns
    -------
    int
        The total number of tokens used by the provided messages.

    Raises
    ------
    NotImplementedError
        If the function is not presently implemented for the given model.

    Notes
    -----
    The function calculates the number of tokens used by messages. The number
    of tokens
    is derived from the encoding of the messages according to the specified
    model.
    If the model is not found in the pre-defined MODELS list, the function will
    fall back
    to using the "cl100k_base" model for token encoding.

    Each message is expected to be in the form of a dictionary with 'role' and
    'content' keys,
    representing the sender role and the content of the message, respectively.
    The function
    calculates the token count considering the special tokens used for message
    encoding,
    such as <im_start> and <im_end>. For future models, token counts may vary,
    so this
    behavior is subject to change.

    The function raises a NotImplementedError if the provided model is not
    supported. Users can refer to the provided link for information on how
    messages are converted to tokens for each specific model.

    Examples
    --------
    >>> messages = [
    ...     {
    ...         'role': 'user',
    ...         'content': "Hello, how are you?"
    ...     },
    ...     {
    ...         'role': 'assistant',
    ...         'content': "I'm doing great! How can I assist you?"
    ...     }
    ... ]
    >>> num_tokens = number_of_tokens(messages)
    >>> print(num_tokens)
    23

    >>> single_message = "This is a test message."
    >>> num_tokens = number_of_tokens(single_message, model="my_custom_model")
    >>> print(num_tokens)
    8
    """
    encoding = get_encoding(model)
    if isinstance(messages, str):
        messages = [
            {
                'role': 'user',
                'content': messages
            }
        ]
    num_tokens = 0
    # if model == MODELS[1]:  # note: future models may
    if True:  # note: future models may deviate from this
        for message in messages:
            # every message follows
            # <im_start>{role/name}\n{content}<im_end>\n
            num_tokens += 4
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if True, the role is omitted
                    num_tokens += -1  # role is always required and 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    raise NotImplementedError(  # TODO choose another error
        f"number_of_tokens() is not presently implemented for model {model}. "
        "See https://github.com/openai/openai-python/blob/main/chatml.md for "
        "information on how messages are converted to tokens."
        ""
    )

def normalize_string(input_string):
    # Remove accents
    normalized_string = unicodedata.normalize('NFKD', input_string).encode('ASCII', 'ignore').decode('utf-8')
    # Remove special characters
    normalized_string = re.sub(r'[^\w\s-]', '', normalized_string)
    # Convert to lowercase
    normalized_string = normalized_string.lower()
    # Replace spaces with dashes
    normalized_string = re.sub(r'\s+', '-', normalized_string)
    return normalized_string

def open_docx_file(filepath):
    """Opens a DOCX file using the default application based on the operating system.

    Args:
        filepath (str): The path to the DOCX file.

    Raises:
        ValueError: If the provided file path is not valid or the file doesn't exist.
        RuntimeError: If the subprocess call to open the file fails.
    """

    if not filepath or not os.path.exists(filepath):
        raise ValueError("Invalid file path or file does not exist.")

    try:
        if platform.system() == "Windows":
            os.startfile(filepath)  # Suitable for most Windows environments
        elif platform.system() == "Darwin":  # macOS
            subprocess.call(["open", filepath])
        elif platform.system() == "Linux":  # Generic Linux handling
            subprocess.call(["xdg-open", filepath])  # Prioritize xdg-open if available
            # Fallback to other likely applications
            for opener in ["libreoffice", "evince", "okular", "docx"]:
                try:
                    subprocess.call([opener, filepath])
                    return  # Success: file opened
                except OSError:
                    pass  # Continue trying other potential openers
        else:
            raise RuntimeError("Unsupported operating system")
    except (OSError, ValueError) as e:
        raise RuntimeError(f"Failed to open '{filepath}': {e}")
