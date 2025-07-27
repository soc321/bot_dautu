from aiogram.fsm.state import State, StatesGroup

class InvestmentStates(StatesGroup):
    waiting_for_package_choice = State()

class DepositStates(StatesGroup):
    waiting_for_amount = State()

class WithdrawStates(StatesGroup):
    waiting_for_amount = State()
