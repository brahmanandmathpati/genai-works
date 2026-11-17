"""Session 21 - BankAssist, built by YOU with LangChain.

This is YOUR file. Copy it into your work repository (the notebook's Section 1 does this for you):
    <your genai-course-work>/s21/bankassist_lc.py
then fill in the five TODOs, one at a time, in order.

Run it after every TODO, from the COURSE repository folder (so your .env is found):
    uv run python $env:WORK_REPO\\s21\\bankassist_lc.py

Each step prints either its result or "not done yet". You never have to finish everything before running.

Rules for using ChatGPT (or any AI assistant) today:
  1. Paste module03/s21_version_card.md into it FIRST - otherwise it writes old LangChain code that will not run.
  2. NEVER paste your .env or your API key.
  3. Ask it to explain or fix YOUR code. You must be able to explain every line you hand in.
"""
import os

from dotenv import find_dotenv, load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

load_dotenv(find_dotenv(usecwd=True), override=True)   # finds the .env in the folder you run from

SYSTEM = ("You are BankAssist, Northwind Bank's assistant. Branches are open 10am-4pm Monday to Friday "
          "and 10am-1pm on Saturday. Home loan rates: 8.5% floating, 9.0% fixed. Answer in 2-3 sentences.\n"
          "More facts you may quote (never invent a number that is not here): personal loan rate 10.5% fixed; "
          "no prepayment penalty on floating-rate loans, 2% of the outstanding amount on fixed-rate loans closed "
          "in the first 12 months; minimum credit score 700; a spouse or blood relative can be a co-applicant; "
          "loan statements are free; disbursal takes 5-7 working days after approval.\n"
          "If asked something not covered here, say you do not have that figure. "
          "Use a tool only for an exact EMI, today's rate, or an affordability check; otherwise answer directly.")


# ================================================================ STEP 1 - one model, one call
def make_llm():
    """Return the chat model.

    TODO 1: return a ChatOpenAI with
        model    = os.environ["MODEL"]
        base_url = os.environ["BASE_URL"]
        api_key  = os.environ["API_KEY"]
        temperature = 0, max_tokens = 1500
    S20 link: this one object replaces OpenAI(...) + client.chat.completions.create(...).
    """
    return ChatOpenAI(model=os.environ["MODEL"], base_url=os.environ["BASE_URL"],
                      api_key=os.environ["API_KEY"], temperature=0, max_tokens=1500)


# ================================================================ STEP 2 - prompt | model | parser
def make_chain(llm):
    """Return a chain that answers {"question": "..."} with plain text.

    TODO 2:
        prompt = ChatPromptTemplate.from_messages([("system", SYSTEM), ("human", "{question}")])
        return prompt | llm | StrOutputParser()
    The | pipe means: the output of the left becomes the input of the right.
    """
    prompt = ChatPromptTemplate.from_messages([("system", SYSTEM), ("human", "{question}")])
    return prompt | llm | StrOutputParser()


# ================================================================ STEP 3 - a tool, as a normal Python function
@tool(parse_docstring=True)
def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> int:
    """Exact monthly EMI for a loan. Use ONLY when the customer asks for an EMI amount.

    Args:
        principal: loan amount in rupees, e.g. 25 lakh = 2500000
        annual_rate: interest rate in percent per year, e.g. 8.5
        tenure_months: total months, e.g. 20 years = 240
    """
    # TODO 3: write the EMI formula and return it ROUNDED to a whole number of rupees.
    #   r = annual_rate / 12 / 100
    #   emi = principal * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1)
    # Check: 25 lakh at 8.5% for 240 months must give 21696.
    # Note: the DOCSTRING above is what the model reads - it is your prompt. Keep parse_docstring=True.
    r = annual_rate / 12 / 100
    return round(principal * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1))


# The tools the model may use, by name. STEP 5 adds get_rate here.
TOOLS = {"calculate_emi": calculate_emi}


# ================================================================ STEP 4 - bind the tools, run YOUR capped loop
def ask(llm_with_tools, question: str, max_steps: int = 3) -> str:
    """Answer one question, letting the model call tools, at most max_steps model calls.

    TODO 4:
        messages = [SystemMessage(SYSTEM), HumanMessage(question)]
        for step in range(1, max_steps + 1):
            ai = llm_with_tools.invoke(messages)
            messages.append(ai)
            if not ai.tool_calls:              # the model answered in words - we are done
                return ai.content
            for call in ai.tool_calls:          # call["name"], call["args"] (a dict), call["id"]
                print(f"  step {step}: {call['name']}({call['args']})")
                messages.append(TOOLS[call["name"]].invoke(call))   # returns a ToolMessage with the SAME id
        return "(stopped: step cap reached)"
    S20 link: no json.loads (args is already a dict) and no hand-made tool_call_id - LangChain does both.
    The loop and its cap are still YOURS. A loop with no cap is an agent - Module 6.
    """
    messages = [SystemMessage(SYSTEM), HumanMessage(question)]
    for step in range(1, max_steps + 1):
        ai = llm_with_tools.invoke(messages)
        messages.append(ai)
        if not ai.tool_calls:              # the model answered in words - we are done
            return ai.content
        for call in ai.tool_calls:          # call["name"], call["args"] (a dict), call["id"]
            print(f"  step {step}: {call['name']}({call['args']})")
            # Homework Fix B: a bad call must not crash the conversation - send the error back to the model
            try:
                if call["name"] not in TOOLS:
                    raise KeyError(f"unknown tool {call['name']!r}")
                messages.append(TOOLS[call["name"]].invoke(call))   # returns a ToolMessage with the SAME id
            except Exception as e:  # noqa: BLE001
                print(f"  step {step}: tool error -> {type(e).__name__}")
                messages.append(ToolMessage(content=f"INVALID: {e}. Answer without a tool if none is needed.",
                                            tool_call_id=call["id"]))
    return "(stopped: step cap reached)"


# ================================================================ HOMEWORK Fix C - a router with structured output
from pydantic import BaseModel, Field


class Route(BaseModel):
    """Does answering this customer question need a tool call?"""
    needs_tool: bool = Field(description="True only if the question asks for an EMI amount or a current interest "
                                         "rate that must be calculated or looked up. False for greetings, "
                                         "branch timings, documents and general questions.")


def needs_tool(llm, question: str) -> bool:
    """Cheap first call: decide whether the question needs a tool. No string matching, so a malformed
    'NO_TOOL' style reply cannot break it - the model must fill the Route schema."""
    router = llm.with_structured_output(Route)
    return router.invoke(question).needs_tool


def answer(llm, question: str) -> str:
    """Router first: plain chain if no tool is needed, the capped tool loop if one is."""
    if needs_tool(llm, question):
        return ask(llm.bind_tools(list(TOOLS.values())), question)
    return make_chain(llm).invoke({"question": question})


# ================================================================ STEP 5 (stretch) - a second tool, two steps in order
# TODO 5: write get_rate(product: str, rate_type: str) -> float as a @tool(parse_docstring=True), with a docstring
# saying what it does and describing both arguments. Rates: home_loan floating 8.5, home_loan fixed 9.0,
# personal_loan fixed 10.5. Then add it to TOOLS:  TOOLS["get_rate"] = get_rate
@tool(parse_docstring=True)
def get_rate(product: str, rate_type: str) -> float:
    """Today's interest rate in percent per year. Use when the customer asks for a rate or needs one for an EMI.

    Args:
        product: "home_loan" or "personal_loan"
        rate_type: "floating" or "fixed" (personal loans are fixed only)
    """
    card = {("home_loan", "floating"): 8.5, ("home_loan", "fixed"): 9.0, ("personal_loan", "fixed"): 10.5}
    return card[(product, rate_type)]


TOOLS["get_rate"] = get_rate


# Parity work (homework 4): S20 had a third tool, so the S21 version gets it too.
@tool(parse_docstring=True)
def check_eligibility(monthly_income: float, existing_emi: float, proposed_emi: float) -> dict:
    """Checks whether a new EMI is affordable: all EMIs together must be at most 50% of monthly income.
    Use when the customer asks if they are eligible or can afford a loan.

    Args:
        monthly_income: take-home income per month in rupees
        existing_emi: EMIs already being paid per month in rupees, 0 if none
        proposed_emi: the new EMI per month in rupees
    """
    foir = (existing_emi + proposed_emi) / monthly_income
    return {"foir": round(foir, 3), "limit": 0.5, "eligible": foir <= 0.5}


TOOLS["check_eligibility"] = check_eligibility


# ================================================================ run me after every TODO
def _step(n, fn):
    try:
        print(f"STEP {n}:", fn())
    except NotImplementedError as e:
        print(f"STEP {n}: not done yet ({e})")
        return False
    return True


def main():
    state = {}

    def s1():
        state["llm"] = make_llm()
        return state["llm"].invoke("Say hello in five words.").content

    def s2():
        return make_chain(state["llm"]).invoke({"question": "What are your branch timings on Saturday?"})

    def s3():
        emi = calculate_emi.invoke({"principal": 2500000, "annual_rate": 8.5, "tenure_months": 240})
        return f"{emi}   {'OK' if emi == 21696 else 'WRONG - expected 21696'}"

    def s4():
        return ask(state["llm"].bind_tools(list(TOOLS.values())),
                   "What is the EMI on a 25 lakh home loan at 8.5% for 20 years?")

    def s5():
        if "get_rate" not in TOOLS:
            raise NotImplementedError("TODO 5, optional stretch")
        return ask(state["llm"].bind_tools(list(TOOLS.values())),
                   "What would my EMI be on a 30 lakh home loan at your floating rate, over 15 years?")

    if _step(1, s1):
        _step(2, s2)
    _step(3, s3)
    if "llm" in state:
        _step(4, s4)
        _step(5, s5)


if __name__ == "__main__":
    main()
