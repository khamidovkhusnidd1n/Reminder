from aiogram.fsm.state import State, StatesGroup

class AddWordState(StatesGroup):
    waiting_for_word = State()
    waiting_for_translation = State()
    waiting_for_definition = State()
    waiting_for_unit = State()
    waiting_for_book = State()
    confirm = State()

class BulkImportState(StatesGroup):
    waiting_for_unit = State()
    waiting_for_book = State()
    waiting_for_data = State()
