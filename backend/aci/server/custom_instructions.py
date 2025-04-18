import json

from openai import OpenAI
from pydantic import BaseModel

from aci.common.db.sql_models import Function
from aci.common.exceptions import CustomInstructionViolation
from aci.common.logging_setup import get_logger

logger = get_logger(__name__)


class ViolationCheckResult(BaseModel):
    is_violated: bool
    justification: str


# TODO: consider adding function schema to the context
def check_for_violation(
    openai_client: OpenAI,
    function: Function,
    function_input: dict,
    custom_instructions: dict[str, str],
    model: str = "gpt-4o-mini",
    temperature: float = 0,
) -> None:
    """
    Check if the function request violates the custom instruction.
    TODO: For external requests failure such as inference calls, we let the request pass.

    Args:
        openai_client: OpenAI client
        function: Function object
        function_input: Function input
        custom_instructions: Custom instructions
        model: Model to use for the violation check
        temperature: Temperature to use for the violation check

    Raises:
        CustomInstructionViolation: If the function request violates the custom instruction
    """
    custom_instruction = custom_instructions.get(function.name)
    if not custom_instruction:
        logger.debug(
            "No custom instruction for the function",
            extra={"function_name": function.name},
        )
        return

    logger.info(
        "Checking for violation of custom instruction",
        extra={"function_name": function.name, "custom_instruction": custom_instruction},
    )

    subject = {
        "function_name": function.name,
        "function_description": function.description,
        "function_input": function_input,
        "custom_instruction": custom_instruction,
    }

    messages = [
        {
            "role": "system",
            "content": (
                "You are assigned the role of a judge to determine whether a function request should be executed. "
                "Each function in our system is defined by a name, a description, and a custom instruction. "
                "When a user submits a request along with specific input arguments, your task is to evaluate the request "
                "against the custom instruction of the chosen function. "
                "Always follow the custom instruction, do not make any assumptions. If the custom instruction does not apply, let the request pass. "
                "Based on this evaluation, decide if the request violates the custom instruction, and provide a clear and concise justification for your decision."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(subject),
        },
    ]

    # TODO: retry.
    # TODO: if the violation check didn't happen due to inference failure, should we let the request pass?
    try:
        response = openai_client.beta.chat.completions.parse(
            model=model,
            messages=messages,  # type: ignore
            response_format=ViolationCheckResult,
            temperature=temperature,
        )
    except Exception:
        # for inference failure, we should let the request pass
        logger.exception("failed inference for violation check, letting the request pass")

    result = response.choices[0].message.parsed

    if result and result.is_violated:
        logger.error(
            "custom instruction violated",
            extra={
                "function_name": function.name,
                "justification": result.justification,
            },
        )
        raise CustomInstructionViolation(
            f"{function.name} execution has been rejected because of custom instruction: {custom_instructions[function.name]}."
            f"justification: {result.justification}"
        )
    else:
        logger.info(
            "custom instruction not violated",
            extra={
                "function_name": function.name,
                "justification": result.justification if result else "unknown",
            },
        )
