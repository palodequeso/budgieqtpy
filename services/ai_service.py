"""
AI Service - Sends budget schedule data to a configurable LLM for analysis.
Uses OpenAI-compatible API (works with Ollama, llama.cpp, vLLM, LM Studio, etc.)
"""

import json
import urllib.request
import urllib.error
from datetime import date
from typing import Optional
from database.database import Database
from shedule.schedule import Schedule


class AIService:
    """Service for AI-powered budget analysis."""

    def __init__(self, db: Database):
        self.db = db

    def get_config(self) -> dict:
        """Get AI configuration from app_settings."""
        return {
            "server_url": self.db.get_setting("ai_server_url") or "",
            "model": self.db.get_setting("ai_model") or "qwen2.5:0.5b",
            "enabled": self.db.get_setting("ai_enabled") == "true",
        }

    def save_config(self, server_url: str, model: str, enabled: bool):
        """Save AI configuration to app_settings."""
        self.db.set_setting("ai_server_url", server_url)
        self.db.set_setting("ai_model", model)
        self.db.set_setting("ai_enabled", str(enabled).lower())

    def build_budget_summary(self, profile_id: int) -> str:
        """Build a detailed extrapolation schedule summary for LLM analysis.

        Focuses on the column-by-column knapsack scheduling output so the LLM
        can catch scheduling errors (wrong income date assignments, negative
        balances, items that should be scheduled earlier, etc.).
        """
        schedule = Schedule()
        schedule.fetch_schedule(self.db, profile_id)
        schedule.build_schedule()

        lines = []
        lines.append("=== EXTRAPOLATION SCHEDULE (KNAPSACK OUTPUT) ===")
        lines.append("")
        lines.append("This is a column-based schedule where each column represents an income date.")
        lines.append("Expenses are assigned to income columns by a knapsack scheduling algorithm.")
        lines.append("Your job is to review whether items are scheduled against the RIGHT income date")
        lines.append("and whether the running balance stays healthy.")
        lines.append("")

        # Budget item reference (so the LLM knows due dates and amounts)
        if schedule.income_budget_items:
            lines.append("INCOME ITEMS (recurring):")
            for item in schedule.income_budget_items:
                lines.append(f"  - {item.name}: ${item.amount:.2f}")
            lines.append("")

        if schedule.expense_budget_items:
            lines.append("EXPENSE ITEMS (recurring):")
            for item in schedule.expense_budget_items:
                lines.append(f"  - {item.name}: ${item.amount:.2f}")
            lines.append("")

        # Column-by-column detailed schedule
        lines.append("=" * 60)
        lines.append("COLUMN-BY-COLUMN EXTRAPOLATION SCHEDULE:")
        lines.append("=" * 60)

        negative_columns = []

        for idx, income_date in enumerate(schedule.sorted_income_dates):
            date_key = income_date.strftime("%Y-%m-%d")
            column = schedule.columns.get(date_key)
            if not column:
                continue

            carry = float(column.starting_balance)
            col_total = float(column.total())
            col_num = idx + 1

            # Flag negative balance columns
            negative_flag = ""
            if col_total < 0:
                negative_flag = "  *** NEGATIVE BALANCE ***"
                negative_columns.append(date_key)
            elif col_total < 50:
                negative_flag = "  ** LOW BALANCE **"

            lines.append(f"\n--- Column {col_num}: {date_key} ---")
            lines.append(f"  Carry-forward balance: ${carry:.2f}")

            # Incomes in this column
            if column.incomes:
                lines.append("  INCOME:")
                for entry in column.incomes:
                    total = float(entry.total())
                    paid_str = "[PAID]" if entry.all_paid() else "[UNPAID]"
                    # Show individual items with due dates
                    for item in entry.items:
                        ei = item.extrapolation_item
                        due = ei.due_date.strftime("%Y-%m-%d") if ei.due_date else "N/A"
                        amt = float(ei.amount)
                        item_paid = "[PAID]" if item.ledger_entry is not None else "[UNPAID]"
                        lines.append(f"    + {entry.budget_item.name}: ${amt:.2f} (due: {due}) {item_paid}")
                    if not entry.items and entry.amount is not None:
                        lines.append(f"    + {entry.budget_item.name if entry.budget_item else entry.name}: ${abs(total):.2f} {paid_str}")

            # Expenses in this column
            if column.expenses:
                lines.append("  EXPENSES:")
                for entry in column.expenses:
                    total = float(entry.total())
                    # Show individual items with due dates
                    for item in entry.items:
                        ei = item.extrapolation_item
                        due = ei.due_date.strftime("%Y-%m-%d") if ei.due_date else "N/A"
                        amt = float(ei.amount)
                        item_paid = "[PAID]" if item.ledger_entry is not None else "[UNPAID]"
                        category_str = f" ({ei.category})" if ei.category else ""
                        lines.append(f"    - {entry.budget_item.name}: ${abs(amt):.2f} (due: {due}) {item_paid}{category_str}")
                    if not entry.items and entry.amount is not None:
                        name = entry.budget_item.name if entry.budget_item else entry.name
                        paid_str = "[PAID]" if entry.all_paid() else "[UNPAID]"
                        lines.append(f"    - {name}: ${abs(total):.2f} {paid_str}")

            income_sum = float(column.income_total())
            expense_sum = float(column.expenses_total())
            lines.append(f"  ────────────────────────")
            lines.append(f"  Income total:  +${income_sum:.2f}")
            lines.append(f"  Expense total: -${abs(expense_sum):.2f}")
            lines.append(f"  Carry forward: ${carry:.2f}")
            lines.append(f"  ENDING BALANCE: ${col_total:.2f}{negative_flag}")

        # Summary of problem columns
        if negative_columns:
            lines.append("")
            lines.append("!" * 60)
            lines.append(f"WARNING: {len(negative_columns)} column(s) have NEGATIVE ending balance:")
            for dc in negative_columns:
                lines.append(f"  - {dc}")
            lines.append("!" * 60)

        # Unscheduled items
        if schedule.unscheduled_entries:
            lines.append("")
            lines.append("UNSCHEDULED ITEMS (not assigned to any income column):")
            for entry in schedule.unscheduled_entries:
                name = entry.budget_item.name if entry.budget_item else (entry.name or "Unknown")
                total = float(entry.total()) if entry.items or entry.amount is not None else 0
                lines.append(f"  ! {name}: ${abs(total):.2f}")

        return "\n".join(lines)

    def analyze(self, profile_id: int) -> dict:
        """Run AI analysis on the budget schedule."""
        config = self.get_config()

        if not config["enabled"] or not config["server_url"]:
            return {"error": "AI analysis is not configured. Set the AI server URL and enable it in Settings."}

        budget_summary = self.build_budget_summary(profile_id)

        prompt = f"""You are a budget scheduling auditor reviewing the output of a knapsack-based bill scheduling algorithm. This algorithm assigns expenses to income date columns.

Your primary job is to catch **scheduling errors** in the extrapolation:

1. **Scheduling Problems**: Expenses assigned to the wrong income date (e.g., a bill due on the 5th scheduled against income arriving on the 15th, when earlier income was available). Items due before their assigned income date arrives.
2. **Balance Issues**: Columns where the ending balance goes negative or dangerously low. This means too many expenses were packed into that income period.
3. **Timing Suggestions**: Expenses that could be moved to a different income column to better balance cash flow across periods.
4. **Paid vs Unpaid Status**: Any anomalies in what's marked paid vs unpaid (e.g., future items marked paid, or past items still unpaid).
5. **Summary**: Brief overall assessment — is the schedule healthy, tight, or in trouble?

Be concise and actionable. Focus on what the scheduling algorithm may have gotten wrong.
Format your response in markdown with headers, bullet points, and **bold** for emphasis.
ABSOLUTELY NEVER SUGGEST INCREASING INCOME! It's okay to say that the budget is too tight or has no or negative margins if that actually is the case.
Also, items like rent, insurance, car payments, water bills, electricity, internet, cell phones, are requirements and shouldn't be suggested to stop paying unless absolutely dire.

It's important to be super kind when helping folks through financial intricacies and to avoid sounding judgmental or negative.
This is because money is often stressful for the types of folks this app is useful for, myself and my family included (from the writer of the code).

This app is not meant to make you rich, it's meant to help build and track a basic budget, not account for investments and such.

PS: DO NOT even mention things like, "Because we can't increase your income, or cut your living expenses, etc"

{budget_summary}"""

        try:
            return self._call_llm(config["server_url"], config["model"], prompt)
        except Exception as e:
            return {"error": str(e)}

    def _call_llm(self, server_url: str, model: str, prompt: str) -> dict:
        """Call an LLM server. Tries Ollama native API first, then OpenAI-compatible /v1/."""
        base = server_url.rstrip("/")
        messages = [{"role": "user", "content": prompt}]

        # Try Ollama native /api/chat first
        endpoints = [
            (f"{base}/api/chat", {"model": model, "messages": messages, "stream": False}),
            (f"{base}/v1/chat/completions", {"model": model, "messages": messages, "temperature": 0.3, "max_tokens": 8000}),
            (f"{base}/chat/completions", {"model": model, "messages": messages, "temperature": 0.3, "max_tokens": 8000}),
        ]

        last_error = None
        for url, body in endpoints:
            payload = json.dumps(body).encode("utf-8")
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=600) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    content = self._extract_content(data)
                    return {"analysis": content, "model": model}
            except urllib.error.HTTPError as e:
                last_error = f"LLM server returned {e.code} at {url}: {e.read().decode('utf-8', errors='replace')}"
                if e.code != 404:
                    raise RuntimeError(last_error)
                # 404 means wrong endpoint, try next
            except urllib.error.URLError as e:
                raise RuntimeError(f"Cannot reach LLM server at {base}: {e.reason}")

        raise RuntimeError(last_error or f"No working LLM endpoint found at {base}")

    def _extract_content(self, data: dict) -> str:
        """Extract the text content from an LLM response.

        Supports:
        - OpenAI format: {"choices": [{"message": {"content": "..."}}]}
        - Ollama native format: {"message": {"content": "..."}}
        - Fallback: convert entire response to string if no known format matches
        """
        # OpenAI-compatible format (also Ollama /v1/ endpoint)
        if "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if isinstance(choice, dict) and "message" in choice:
                msg = choice["message"]
                if isinstance(msg, dict) and "content" in msg:
                    return msg["content"]
            # Some endpoints put content directly on the choice
            if isinstance(choice, dict) and "content" in choice:
                return choice["content"]
            # If choice is a string, return it
            if isinstance(choice, str):
                return choice

        # Ollama native /api/chat format
        if "message" in data and isinstance(data["message"], dict):
            if "content" in data["message"]:
                return data["message"]["content"]

        # Ollama native /api/generate format
        if "response" in data and isinstance(data["response"], str):
            return data["response"]

        # Last resort: return the raw JSON so the user sees something useful
        # instead of a crash or empty result
        return json.dumps(data, indent=2)
