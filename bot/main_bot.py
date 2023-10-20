import asyncio

from django.utils import timezone
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from asgiref.sync import sync_to_async

from django.conf import settings

from bot.models import Appointment, User
from datetime import datetime, timedelta

bot = AsyncTeleBot(settings.TOKEN_BOT, parse_mode='HTML')


@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    # Создаем пользователя в базе данных с id-telegram
    user, created = User.objects.get_or_create(username=message.chat.username, defaults={'client_id': message.chat.id})
    if created:
        user.save()
        await bot.reply_to(message, 'Добро пожаловать! Вы были успешно зарегистрированы.')
    else:
        await bot.reply_to(message, 'Добро пожаловать снова!')

    # Отправляем кнопку для создания записи
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    item = types.KeyboardButton("Создать запись")
    markup.add(item)
    await bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Создать запись")
async def create_appointment(message):
    # Здесь начнется процесс создания записи, вы можете задавать вопросы и ожидать ответы от пользователя.
    await bot.send_message(message.chat.id, "Пожалуйста, введите свой номер телефона:")
    bot.register_next_step_handler(message, process_phone_number)


def process_phone_number(message):
    # Здесь вы можете получить номер телефона из message.text и сохранить его в базе данных или как-то еще обработать.
    phone_number = message.text

    # Пример сохранения номера телефона в базе данных
    user = User.objects.get(username=message.chat.username)
    user.phone_number = phone_number
    user.save()

    # Задайте следующий вопрос или выполняйте действия, которые вам нужны.

# Остальной код оставьте без изменений
