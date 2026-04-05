from aiogram.fsm.state import State, StatesGroup


class ReviewState(StatesGroup):
    viewing = State()
    editing_description = State()


class ScheduleTimeState(StatesGroup):
    waiting_input = State()


class ScheduleContentState(StatesGroup):
    waiting_input = State()


class InstagramState(StatesGroup):
    waiting_challenge_code = State()


class LogoUploadState(StatesGroup):
    waiting_file = State()


class BroadcastState(StatesGroup):
    waiting_message = State()


class SubscriptionAddState(StatesGroup):
    waiting_input = State()
