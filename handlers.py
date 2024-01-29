from aiogram import types, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart, StateFilter, CommandObject, CREATOR
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from database import pool, execute_update_query, execute_select_query , _format_kwargs, get_ydb_pool
from service import generate_options_keyboard, get_question, new_quiz, get_quiz_index, update_quiz_index, get_result
import os
import ydb


router = Router()

YDB_ENDPOINT = os.getenv("YDB_ENDPOINT")
YDB_DATABASE = os.getenv("YDB_DATABASE")

pool = get_ydb_pool(YDB_ENDPOINT, YDB_DATABASE)




@router.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):

    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    
    await callback.message.answer("Верно!")
    
    # Обновление номера текущего вопроса в базе данных
    current_question_index = await get_quiz_index(callback.from_user.id)
    current_question_index += 1
    result = await get_result(callback.from_user.id)
    result+=1
    await update_quiz_index(callback.from_user.id, current_question_index, result)


    if current_question_index < 11:
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен! Ваш результат: {result}")

  
@router.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    
    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)
    result = await get_result(callback.from_user.id)

    query = """
    DECLARE $current_question_index as Uint64;

    SELECT OptionA, OptionB, OptionC, OptionD, CorrectAnswer
    FROM Questions1
    WHERE QuestionID == $current_question_index;
    """
    
    results = execute_select_query(pool, query, current_question_index=current_question_index)
    opts = [results[0]['OptionA'], results[0]['OptionB'], results[0]['OptionC'], results[0]['OptionD']]
    correct_index = results[0]['CorrectAnswer'] - 1
    correct_answer = opts[correct_index]
    
    await callback.message.answer(f"Неправильно. Правильный ответ: {correct_answer.decode('utf-8')} ")
    
    
    
    
    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index, result)


    if current_question_index < 11:
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен! Ваш результат: {result} ")

        


# Хэндлер на команду /start
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))


# Хэндлер на команду /quiz
@router.message(F.text=="Начать игру")
@router.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    result=0
    await message.answer_photo('https://storage.yandexcloud.net/chichik/photo_2024-01-28_02-22-31.jpg')
    await message.answer(f"Давайте начнем квиз!")
    await new_quiz(message)
    

