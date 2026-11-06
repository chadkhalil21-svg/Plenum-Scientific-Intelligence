"""Conservative heuristics to reject empty or obvious prompt-echo model output."""


def assess_answer(answer, role):
    if not isinstance(answer, str) or len(answer.strip()) < 80:
        return {"acceptable": False, "reason": "empty_or_too_short"}
    forbidden = ("Scientific hypothesis proposer: Provide two falsifiable",
                 "Scientific hypothesis proposer: provide two falsifiable",
                 "Independent scientific critic: identify weaknesses",
                 "Independent scientific critic: Identify weaknesses")
    if any(x.casefold() in answer.casefold() for x in forbidden):
        return {"acceptable": False, "reason": "repeated_instruction"}
    if answer.count(answer[:45]) >= 3:
        return {"acceptable": False, "reason": "repetition"}
    return {"acceptable": True, "reason": "basic_echo_screen_only_not_scientific_validation"}
