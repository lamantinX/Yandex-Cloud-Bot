from  database import pool, execute_update_query, execute_select_query
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import types
from database import quiz_data


def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data="right_answer" if option == right_answer else "wrong_answer")
        )

    builder.adjust(1)
    return builder.as_markup()





async def get_question(message, user_id):
    question_index = await get_quiz_index(user_id)

    query = """
    DECLARE $question_index as Uint64;

    SELECT QuestionText, OptionA, OptionB, OptionC, OptionD, CorrectAnswer
    FROM Questions1
    WHERE QuestionID == $question_index;
    """
    
    result = execute_select_query(pool, query, question_index=question_index)

    if result:
        question_text = result[0]['QuestionText']
        opts = [result[0]['OptionA'], result[0]['OptionB'], result[0]['OptionC'], result[0]['OptionD']]
        correct_index = result[0]['CorrectAnswer'] - 1

        kb = generate_options_keyboard(opts, opts[correct_index])
        await message.answer(question_text, reply_markup=kb)



async def new_quiz(message):
    user_id = message.from_user.id
    current_question_index = 1
    result=0
    await update_quiz_index(user_id, current_question_index, result)
    await get_question(message, user_id)


async def get_quiz_index(user_id):
    get_user_index = f"""
        DECLARE $user_id AS Uint64;

        SELECT question_index
        FROM `quiz_state`
        WHERE user_id == $user_id;
    """
    results = execute_select_query(pool, get_user_index, user_id=user_id)

    if len(results) == 0:
        
        return 0
    if results[0]["question_index"] is None:
        
        return 0
    return results[0]["question_index"]    



async def get_result(user_id):
    get_user_index = f"""
        DECLARE $user_id AS Uint64;

        SELECT result
        FROM `quiz_state`
        WHERE user_id == $user_id;
    """
    results = execute_select_query(pool, get_user_index, user_id=user_id)

    if len(results) == 0:
        
        return 0
    if results[0]["result"] is None:
        
        return 0
    return results[0]["result"]     
    

async def update_quiz_index(user_id, question_index, result):
    set_quiz_state = f"""
        DECLARE $user_id AS Uint64;
        DECLARE $question_index AS Uint64;
        DECLARE $result AS Uint64;

        UPSERT INTO `quiz_state` (`user_id`, `question_index`, `result`)
        VALUES ($user_id, $question_index, $result);
    """

    execute_update_query(
        pool,
        set_quiz_state,
        user_id=user_id,
        question_index=question_index,
        result=result
    )
    
