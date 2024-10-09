from cat.mad_hatter.decorators import hook, plugin
from datetime import datetime
from pydantic import BaseModel, Field


class PluginSettings(BaseModel):
    input_token_price_per_milion: float = Field(
        default=0,
        description="Set your price per milion input token to get a live cost estimation"
    )

    output_token_price_per_milion: float = Field(
        default=0,
        description="Set your price per milion output token to get a live cost estimation"
    )

    currency_string: str = Field(
        default='€'
    )


@plugin
def settings_model():
    return PluginSettings


@hook
def before_cat_reads_message(user_message_json, cat):
    cat.working_memory.start_time = datetime.now()

    return user_message_json


@hook
def before_cat_sends_message(message, cat):
    cat.working_memory.end_time = datetime.now()

    llm_name = next((value for key, value in cat._llm.__dict__.items() if "model" in key.lower()), 'undefined')
    input_tokens = [query.input_tokens for query in cat.working_memory.model_interactions if query.model_type == 'llm']
    output_tokens = [query.output_tokens for query in cat.working_memory.model_interactions if query.model_type == 'llm']
    minutes, seconds = divmod((cat.working_memory.end_time - cat.working_memory.start_time).total_seconds(), 60)
    time_string = f"{minutes}m {seconds:.0f}s" if minutes > 0 else f"{seconds:.0f}s"

    settings = cat.mad_hatter.get_plugin().load_settings()
    price_per_input_token = settings['input_token_price_per_milion']/1e6
    price_per_output_token = settings['output_token_price_per_milion']/1e6

    message.content += f'\n---\n✨ Generated in {time_string} with `{llm_name}` | input {(sum(input_tokens) / 1000):.2f}K tok ({settings["currency_string"]} {sum(input_tokens) * price_per_input_token}) output {(sum(output_tokens) / 1000):.2f}K tok ({settings["currency_string"]} {sum(output_tokens) * price_per_output_token}) ✨'

    return message

@hook
def before_agent_starts(agent_input, cat):
    # When the LLM reads the chat history, it will lie generating the string "Generated in x seconds"
    # this is not an intended behavour, so we delete each occurrence of that string

    if len(cat.working_memory.history) >= 2:
        cat.working_memory.history[-2]['message'] = "\n".join([line for line in cat.working_memory.history[-2]['message'].splitlines() if '✨' not in line])

    return agent_input