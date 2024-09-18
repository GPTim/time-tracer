from cat.mad_hatter.decorators import hook
from datetime import datetime


@hook
def before_cat_reads_message(user_message_json, cat):
    cat.working_memory.start_time = datetime.now()

    return user_message_json


@hook
def before_cat_sends_message(message, cat):
    cat.working_memory.end_time = datetime.now()

    llm_name = next((value for key, value in cat._llm.__dict__.items() if "model" in key.lower()), 'undefined')
    message.content += f'\n✨ _Generated in {(cat.working_memory.end_time - cat.working_memory.start_time).total_seconds():.0f}s using {llm_name} as LLM_ ✨'

    return message

@hook
def before_agent_starts(agent_input, cat):
    # When the LLM reads the chat history, it will lie generating the string "Generated in x seconds"
    # this is not an intended behavour, so we delete each occurrence of that string

    if len(cat.working_memory.history) >= 2:
        cat.working_memory.history[-2]['message'] = "\n".join([line for line in cat.working_memory.history[-2]['message'].splitlines() if '✨ _Generated' not in line])

    return agent_input