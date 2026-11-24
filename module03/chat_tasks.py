"""Session 19 data - chat state & memory windows: BankAssist, a multi-turn bank product-FAQ assistant.

A new, standalone running example - not the Session 16/18 ticket classifier continued. Multi-turn memory is
easiest to feel with a conversation that NEEDS an early turn to answer a late one, and a classifier that labels
one ticket and stops never creates that need.

  BANKASSIST_SYSTEM   the standing system prompt: BankAssist's role, tone, and the small FAQ fact sheet it may
                       quote (rates, fees, eligibility) - a fixed knowledge base, not a RAG system (that is
                       Module 4's job, on purpose).
  RECALL_PROBE         a scripted 17-turn conversation. Turn 2 plants a fact ONLY the conversation itself can
                       supply - a reference number and two figures the customer states about themselves -
                       nothing a model could answer correctly from BANKASSIST_SYSTEM alone. Turns 3-16 are
                       genuine, unrelated FAQ questions: the filler a real conversation accumulates. Turn 17
                       asks for the planted fact back.
  RECALL_TOKEN         the exact substring that must appear in turn 17's reply for recall to count as success.
  WINDOW_SIZE           how many of the most recent MESSAGES a sliding window keeps (not turns - a turn is a
                       user message plus the assistant's reply, so WINDOW_SIZE=6 keeps roughly the last 3 turns).
  SUMMARY_EVERY        how many turns pass before older turns are compressed again.
"""
from __future__ import annotations

# ---------------------------------------------------------------- the standing contract (S14's term, every call)
BANKASSIST_SYSTEM = """---
name: bankassist
version: 1
owner: retail products
---
# Role
You are BankAssist, a conversational assistant for Northwind Bank's retail customers. You answer questions
about the bank's loan and account products in plain, friendly language, and you remember what the customer has
told you earlier in THIS conversation - their own figures, reference numbers, and which product they asked about.

# Facts you may quote (never invent a number that is not on this list)
- Personal loan interest rate: 10.5% to 14% per annum, depending on credit score.
- Home loan interest rate: 8.5% to 9.5% per annum (floating), 9.0% to 9.8% per annum (fixed).
- Loan processing fee: 1% + GST for salaried applicants, 1.5% + GST for self-employed applicants.
- Maximum personal loan tenure: 5 years. Maximum home loan tenure: 20 years (up to 30 years for amounts under
  Rs 50 lakh).
- No prepayment penalty on floating-rate loans; 2% of the outstanding amount on fixed-rate loans foreclosed
  within the first 12 months.
- Minimum credit score for a new loan: 700. A spouse or blood relative may be added as a co-applicant on any
  loan product.
- Loan account statements are free, any time, through net banking or at a branch.
- Branches are open 10am-4pm Monday to Friday, 10am-1pm on Saturday, closed Sunday.
- Loan applications can be started online; final disbursal typically takes 5-7 working days after approval.

# House rules
1. Only use the facts listed above. If asked something this list does not cover, say plainly that you do not
   have that figure and offer to connect the customer to a relationship manager - never invent a number.
2. Remember what the customer tells you about themselves earlier in this conversation (income, loan amount,
   reference numbers, which product they are asking about) and use it in later answers without asking again.
3. Keep answers to two or three sentences unless the customer asks for more detail.

# Reply format
Plain conversational text. No tags, no markdown headers, no bullet lists unless the customer asks for a list.
"""

# ---------------------------------------------------------------- the recall probe: one scripted 17-turn chat
# The exact substring a correct recall must contain. A reference-number token, not a rupee figure, because a
# model is far more likely to reproduce an alphanumeric code verbatim than to restate a number identically -
# which makes an automated check meaningfully more reliable for a teaching example.
RECALL_TOKEN = "77042"

RECALL_PROBE = [
    # turn 1 - opens the conversation, nothing to remember yet
    "Hi, I'm thinking about taking out a loan but I'm not sure where to start.",
    # turn 2 - THE PLANTED FACT: a reference number, and figures only the customer could supply
    "Before we go further, here's my enquiry reference number: LN-77042-BLR. I'm self-employed, my annual "
    "income is about Rs 8.5 lakh, and I'm looking at a home loan of around Rs 25 lakh over 20 years.",
    # turns 3-16 - genuine, unrelated FAQ filler: the shape of a real conversation
    "What are your home loan interest rates right now?",
    "What documents will I need to apply?",
    "Do you offer a top-up loan on an existing home loan?",
    "What's the maximum tenure you offer on a personal loan?",
    "Is there a prepayment penalty if I pay off a floating-rate loan early?",
    "Can I add my spouse as a co-applicant on the home loan?",
    "How would I check the status of my application once I've applied?",
    "Do you have any guidance on tax benefits for home loan interest?",
    "What are your branch timings on Saturdays?",
    "Is it possible to apply for the loan entirely online?",
    "What credit score do I need to qualify?",
    "Can I make a part-payment on the loan at any time, or only on certain dates?",
    "Roughly how long does disbursal take once the loan is approved?",
    "Is there any charge for getting a loan account statement later on?",
    # turn 17 - THE RECALL QUESTION: can only be answered from turn 2, still being in the call
    "Can you remind me of the reference number I gave you earlier in this chat?",
]

# ---------------------------------------------------------------- the two fixes' knobs
WINDOW_SIZE = 6       # most recent MESSAGES kept (system message is always kept on top of this)
SUMMARY_EVERY = 6      # compress older turns again every this-many turns
