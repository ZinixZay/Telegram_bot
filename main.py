from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from pyowm import OWM
import pymorphy2
import emoji
import datetime
from easygoogletranslate import EasyGoogleTranslate
import pyrebase
from config import *
import markups as nav


bot = Bot(token=bot_token)

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

morph = pymorphy2.MorphAnalyzer()

owm = OWM(owm_token)
mgr = owm.weather_manager()

dp = Dispatcher(bot)

translator = EasyGoogleTranslate(
    source_language='en',
    target_language='ru',
    timeout=10
)


async def send_msg(chat_id, msg):
    await bot.send_message(chat_id, msg)


async def greetings(sender_id):
    await bot.send_message(sender_id, emoji.emojize('День добрый \U0001F60A'), reply_markup=nav.mainMenu)


async def give_info(sender_id):
    await bot.send_message(sender_id, emoji.emojize('О чем вы хотите узнать? \U0001F914'), reply_markup=nav.infoMenu)


async def weather_info(sender_id):
    msg_part_1 = emoji.emojize('\U0001F387 Узнайте погоду в любом городе! \U0001F387\n\n')
    msg_part_2 = emoji.emojize('\U0001F534 Пример команды:\n\n')
    msg = f'{msg_part_1}' \
          f'{msg_part_2}' \
          f'/погода москва\n\n' \
          f'Чтобы сократить команду, достаточно написать лишь\n\n' \
          f'/п москва'
    await send_msg(sender_id, msg)


async def mailing_info(sender_id):
    msg_part_1 = emoji.emojize('\U0001F563')
    msg_part_2 = emoji.emojize('\U0000274C')
    msg = f'{msg_part_1} Установите время рассылки погоды вашего города! {msg_part_1}\n' \
          f'Пример команды:\n\n' \
          f'/t 08:30 москва\n\n' \
          f'{msg_part_2} Чтобы удалить рассылку, напишите  {msg_part_2}\n\n' \
          f'/t удалить'
    await send_msg(sender_id, msg)


async def set_mailing(sender_id, when):
    data = db.child('users').get().val()
    if when[-1] in mailing_delete:
        try:
            del data[str(sender_id)]
            msg = emoji.emojize('\U00002705')
            await send_msg(sender_id, f'Рассылка удалена {msg}')
        except KeyError:
            msg = emoji.emojize('\U0001F615')
            await send_msg(sender_id, f'В этом чате нет рассылки{msg}')
        db.child('users').set(data)
        return
    when_t = when[-2]
    when_c = when[-1]

    if when_t not in mailing_delete:
        for i in rzd:
            if len(when_t.split(i)) == 2:
                ch = when_t.split(i)[0]
                mn = when_t.split(i)[1]
                if len(ch) == 2 and len(mn) == 2 and 0 <= int(ch) <= 24 and 0 <= int(mn) <= 60:
                    break
            try:
                observation = mgr.weather_at_place(morph.parse(when_c)[0].inflect({'nomn'}).word)
            except AttributeError:
                if when_c != '':
                    msg = emoji.emojize('\U0001F615')
                    await send_msg(sender_id, f'Проверьте корректность вашей команды {msg}\n'
                                              f'Пример:\n'
                                              f'/t 08:30 москва')
                    return
        else:
            msg = emoji.emojize('\U0001F615')
            await send_msg(sender_id, f'Проверьте корректность вашей команды {msg}\n'
                                      f'Пример:\n'
                                      f'/t 08:30 москва')
            return
        msg = emoji.emojize('\U00002705')
        await send_msg(sender_id, f'Рассылка погоды в городе "{when_c}" установлена на {ch} {mn} {msg}')
        data[sender_id] = {'hour': ch,
                           'minute': mn,
                           'city': when_c}
    else:
        try:
            del data[str(sender_id)]
            msg = emoji.emojize('\U00002705')
            await send_msg(sender_id, f'Рассылка удалена {msg}')
        except KeyError:
            msg = emoji.emojize('\U0001F615')
            await send_msg(sender_id, f'В этом чате нет рассылки{msg}')
    db.child('users').set(data)


async def bot_info(sender_id):
    msg = 'Бот написан для Хакатона от AllStack\n' \
          'Функционал: показывает время и устанавливает время рассылки, которая присылает погоду в конкретном городе'
    print('1')
    await send_msg(sender_id, msg)


async def weather_msg(given, sender_id):
    try:
        observation = mgr.weather_at_place(morph.parse(given[-1])[0].inflect({'nomn'}).word)
    except AttributeError:
        await bot.send_message(sender_id, emoji.emojize('Город не найден \U0001F614'))
        return
    except Exception:
        await bot.send_message(sender_id, emoji.emojize('Проверьте корректность вашей команды \U0001F641'))
        return

    city = emoji.emojize('\U0001F306 В ' +
                         morph.parse(given[-1])[0].inflect({'loct'}).word.capitalize() + ' \U0001F306')
    w = observation.weather

    s = emoji.emojize(plus_st(w.status).capitalize())

    temp = round(w.temperature('celsius')['temp'], 1)
    m_temp = round(w.temperature('celsius')['feels_like'], 1)

    msg = f'{city.capitalize()}\n' \
          f'{s}\n' \
          f'Температура: {temp}°\n' \
          f'Ощущается как: {m_temp}°'

    await bot.send_message(sender_id, msg)


def plus_st(sit):
    if sit.lower() == 'clear':
        return '\U0001F506 Ясненько \U0001F506'
    elif sit.lower() == 'clouds':
        return '\U0001F325 Облачка \U0001F325'
    elif sit.lower() == 'mist' or sit.lower() == 'fog':
        return '\U0001F32B Туманно \U0001F32B'
    elif sit.lower() == 'snow':
        return '\U0001F328 Снежок \U0001F328'
    elif sit.lower() == 'rain':
        return '\U0001F326 Дождик \U0001F326'


@dp.message_handler(commands=starting_commands)
async def starting(message: types.Message):
    sender_id = message['chat']['id']
    await greetings(sender_id)


@dp.message_handler(commands=weather_commands)
async def weather(message: types.Message):
    sender_id = message['chat']['id']
    s = message['text'].lower().split()
    await weather_msg(s, sender_id)


@dp.message_handler(commands=mailing_commands)
async def mailing(message: types.Message):
    sender_id = message['chat']['id']
    s = message['text'].lower().split()
    await set_mailing(sender_id, s)


@dp.message_handler(commands=info_commands)
async def info(message: types.Message):
    sender_id = message['chat']['id']
    await give_info(sender_id)


@dp.message_handler()
async def main(message: types.Message):
    sender_id = message['chat']['id']
    com_parse = emoji.demojize(message['text'])
    if com_parse == secret_code:
        await timer()
    elif com_parse == ':information: Информация':
        await give_info(sender_id)
    elif com_parse == '☰ В меню':
        await bot.send_message(sender_id, emoji.emojize('Назад в меню \U000025C0'), reply_markup=nav.mainMenu)
    elif com_parse == ':thermometer: Погода':
        await weather_info(sender_id)
    elif com_parse == ':envelope_with_arrow: Рассылка':
        await mailing_info(sender_id)
    elif com_parse == ':robot: О боте':
        await bot_info(sender_id)


async def timer():
    data = db.child('users').get().val()
    hours = str(datetime.datetime.now()).split(':')[0][len(str(datetime.datetime.now()).split(':')[0]) - 2:]
    minutes = str(datetime.datetime.now()).split(':')[1]
    for i in data.keys():
        if i != 'system':
            if data[i]['hour'] == str(hours) and data[i]['minute'] == str(minutes):
                await weather_msg([data[i]['city']], i)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
