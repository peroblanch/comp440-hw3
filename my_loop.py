"""Your agent's loop, which you design in step 1a. The homework page says what the
loop is for, under "1a. Design the loop" (also in instructions/part1.md), and the
check tells you each rule it must follow when your loop breaks it.

You design the loop as an outline in plain words, in WRITEUP.md under 1a. The
loop below the line that says where it goes is Claude's translation of that
outline, written with the parts in loop_parts.py: each line of your outline is a
comment, with about one line of Python for it under it. To change the loop,
change your outline and ask Claude to translate it again.

Check it after each translation. The check uses a scripted stand-in for the
model and for Wikipedia, so it needs no key and costs nothing:

    uv run python check_loop.py

Part 0 runs the agent on the reference loop. Once every rule passes, the agent
runs on this loop and no other: the runs of 1c and later need it to pass.
"""

import anthropic

# The names below include every one the file had before the parts, so that a loop written
# then still runs.
from agent import (ACCEPTED, DECLINED, INSTRUCTIONS, MAX_REJECTED, MAX_STEPS, MODEL, NO_ANSWER,
                   OUT_OF_STEPS, RAN_OUT, REJECTED, REJECTED_TOO_OFTEN, REMINDED, REMINDER,
                   TOOLS, answer_problem, clean_answer, finish, run_tool)
from loop_parts import Conversation


def run_agent(claim, client=None, max_steps=MAX_STEPS, lookup=run_tool):
    """Check one claim. Returns what talk.accept() or talk.stop() returns."""
    client = client or anthropic.Anthropic()
    system = INSTRUCTIONS.read_text()
    messages = [{"role": "user", "content": f"Claim: {claim}"}]
    trace, read_so_far = [], []
    talk = Conversation(claim, client, system, messages, trace, read_so_far, lookup)
    steps = 0          # lookups made so far
    rejected = 0       # answers sent back so far

    # Your loop should repeatedly call the model with the message history so far, and ask for
    # its next step. It should check whether the model has given an answer yet. If not, it should
    # make the lookups that step asks for, and add what they return to the history. It should
    # also pay attention to whether the loop has reached its limit: a claim that runs out of
    # lookups cannot be decided.
    # ---- your loop goes below this line (step 1a) ----

    # Ask the model for tool calls based on the prompt.
    reply = talk.ask()

    # Set steps to 0 and reminded to false.
    # (steps is already 0 above)
    reminded = False

    # Loop:
    while True:

        # If the model has given responses, and there is an answer tool call, stop looping and submit the answer.
        if talk.asked > 0 and reply.answer:
            return talk.accept(reply.answer, steps)

        # If there are no lookup or tool calls requested, stop looping with no answer.
        if not reply.calls:
            return talk.stop(NO_ANSWER, steps)

        # If reminded is true:
        if reminded:

            # Stop looping with no answer.
            return talk.stop(RAN_OUT, steps)

        # For each requested lookup in the reply:
        for call in reply.lookups:

            # If steps is less than max_steps:
            if steps < max_steps:

                # Perform the lookup, add its result to the full message response, and increase steps by 1.
                talk.give(call, talk.run(call))
                steps += 1

            # Otherwise:
            else:

                # Add the ready-made limit-reached result for this lookup to the full message response.
                talk.give(call, OUT_OF_STEPS.format(n=max_steps))

        # If steps has reached max_steps:
        if steps >= max_steps:

            # Add a line to the full message response instructing the model to provide an answer now.
            talk.results.append({"type": "text", "text": REMINDER})

            # Set reminded to true.
            reminded = True

        # Send the updated message to the model to get a new response, and repeat the loop.
        talk.send_results()
        reply = talk.ask()
