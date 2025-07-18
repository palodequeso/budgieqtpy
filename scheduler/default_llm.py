from datetime import date
import asyncio

from database.budget_item import BudgetItem
from database.database import Database
from shedule.schedule import Schedule
from shedule.schedule_entry import ScheduleEntry
from .base import BaseScheduler
from ollama import AsyncClient

class DefaultLLM(BaseScheduler):
    push_expenses_up: bool = False
    profile_id: int = None
    start_date: date = None
    end_date: date = None
    schedule: Schedule = None
    database: Database = None
    income_budget_items: list[BudgetItem] = None
    expense_budget_items: list[BudgetItem] = None
    llm_model: str = "llama3.2"

    def __init__(self, database, profile_id):
        super().__init__(database, profile_id)
        self.income_budget_items = []
        self.expense_budget_items = []
        self.unscheduled_schedule_entries: list[ScheduleEntry] = []
        for budget_item in self.budget_items:
            if budget_item.type == "Income":
                self.income_budget_items.append(budget_item)
            else:
                self.expense_budget_items.append(budget_item)
        asyncio.run(self.chat())

    async def chat(self):
        prompt = 'Can you create a full year csv of a budget for the following income and expenses? Income: '
        for item in self.income_budget_items:
            periods = ''
            first = True
            for period in item.periods:
                if not first:
                    periods += ' and '
                periods += f'{period.type} of {period.value} '
                first = False
            prompt += f'{item.name} of {item.amount} every {periods}, '
        prompt += ' Expenses: '
        for item in self.expense_budget_items:
            periods = ''
            first = True
            for period in item.periods:
                if not first:
                    periods += ' and '
                periods += f'{period.type} of {period.value} '
                first = False
            prompt += f'{item.name} of {item.amount} every {periods}, '
        prompt += f''' for one year, starting from {date.today().strftime("%Y-%m-%d")}.
            It should account for every pay and bill's amount and periods, slotting each bill into various pay days.
            Please respond with the schedule as a csv string with dates and amounts and totals,
            and including rollver to the next pay period. Expenses should subtract from Income.
            This should result in a grid for the year where incomes are columns and expenses are rows.
            Make it look like this CSV example:
            Date,2025-07-01,2025-07-15,2025-08-01,2025-08-15,2025-09-01,2025-09-15,2025-10-01,2025-10-15,2025-11-01,2025-11-15,2025-12-01,2025-12-15,2026-01-01
            Carryover,0,-2000,-1850,-650,-1850,-650,-1850,-650,-1850,-650,-3200,-1300,-2350
            Pay,2000,,,,,,,,,,,,
            Rent,-1000,-1000,,-1000,,-1000,,-1000,,-2000,,-1000,
            Car,-300,,-300,,-300,,-300,,-300,,-600,,-300
            SchoolLoan,,-500,,-500,,-500,,-500,,-500,,-1000,
            Food,-200,-100,-100,-100,-100,-100,-100,-100,-100,-200,-200,-100,-100
            Gas,-100,-50,-50,-50,-50,-50,-50,-50,-50,-100,-100,-50,-50
            Groceries,-400,-200,-200,-200,-200,-200,-200,-200,-200,-400,-400,-200,-200
            Subtotal,-2000,-1850,-650,-1850,-650,-1850,-650,-1850,-650,-3200,-1300,-2350,-650
            Total,0,-3850,-2500,-2500,-2500,-2500,-2500,-2500,-2500,-3850,-4500,-3650,-3000'''
        print(prompt)
        message = {'role': 'user', 'content': prompt}
        async for part in await AsyncClient().chat(model=self.llm_model, messages=[message], stream=True):
            print(part['message']['content'], end='', flush=True)
