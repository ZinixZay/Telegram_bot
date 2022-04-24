from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import emoji

btnMain = KeyboardButton(emoji.emojize('\U00002630 В меню'))

''' Main Menu '''
btnWeather = KeyboardButton(emoji.emojize('\U00002139 Информация'))
btnBot = KeyboardButton(emoji.emojize('\U0001F916 О боте'))
mainMenu = ReplyKeyboardMarkup(resize_keyboard=True).add(btnWeather, btnBot)


''' Info Menu '''
btnIWeather = KeyboardButton(emoji.emojize('\U0001F321 Погода'))
btnITimer = KeyboardButton(emoji.emojize('\U0001F4E9 Рассылка'))
infoMenu = ReplyKeyboardMarkup(resize_keyboard=True).add(btnIWeather, btnITimer, btnMain)