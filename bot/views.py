import telebot
from django.http import HttpResponse
from telebot import types

from bot.models import User, Appointment, Service
from django_telegram import settings

bot = telebot.TeleBot(settings.BOT_TOKEN)


def index(request):
    if request.method == "POST":
        update = telebot.types.Update.de_json(request.body.decode('utf-8'))
        bot.process_new_updates([update])

    return HttpResponse('<h1>Ты подключился!</h1>')


@bot.message_handler(commands=['start'])
def start(message: telebot.types.Message):
    # Получите информацию о пользователе
    client_id = message.from_user.id
    username = message.from_user.username

    # Проверьте, существует ли пользователь с таким id
    user, created = User.objects.get_or_create(client_id=client_id, defaults={'username': username})

    if created:
        user.save()

    name = user.username if user.username else user.first_name

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item = types.KeyboardButton("Записаться на приём🤗")
    markup.add(item)

    bot.send_message(
        message.chat.id,
        f'Привет, {name}!❤️\n'
        f'Я бот, который поможет вам записаться на приём в салон красоты.😊\n\n'
        f'Чтобы записаться, нажмите кнопку👇.',
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == "Записаться на приём🤗")
def start_appointment(message: telebot.types.Message):
    # Запрос номера телефона
    bot.send_message(message.chat.id, "Для записи на приём, пожалуйста, укажите ваш номер телефона (например, +79005965245):")
    bot.register_next_step_handler(message, process_phone_number)


def process_phone_number(message):
    phone_number = message.text

    if len(phone_number) >= 10:
        markup = types.ReplyKeyboardRemove()
        bot.send_message(
            message.chat.id,
            "Укажите дату и время приёма (например, 2023-09-15 15:00):",
            reply_markup=markup
        )
        bot.register_next_step_handler(message, process_appointment_datetime, phone_number)
    else:
        # В случае неверного номера телефона отправляем сообщение об ошибке
        bot.send_message(
            message.chat.id,
            "Номер телефона введен неверно. Пожалуйста, укажите номер в правильном формате (например, +79005965245):"
        )


def process_appointment_datetime(message, phone_number):
    appointment_datetime = message.text
    if len(appointment_datetime) >= 16:

        # Запрашиваем выбор услуги
        services = Service.objects.all()
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        for service in services:
            markup.add(service.name)

        bot.send_message(
            message.chat.id,
            "Выберите услугу из списка:",
            reply_markup=markup
        )
        bot.register_next_step_handler(message, process_selected_service, phone_number, appointment_datetime)
    else:
        # В случае неверного формата даты и времени отправляем сообщение об ошибке
        bot.send_message(
            message.chat.id,
            "Дата и время приёма введены неверно. Пожалуйста, укажите их в правильном формате (например, 2023-09-15 15:00):"
        )


def process_selected_service(message, phone_number, appointment_datetime):
    selected_service_name = message.text

    # Поиск выбранной услуги
    selected_service = Service.objects.filter(name=selected_service_name).first()

    if selected_service:
        # Создание записи о приёме в базе данных
        user_id = message.from_user.id
        user, _ = User.objects.get_or_create(client_id=user_id, defaults={'username': message.chat.username})
        appointment = Appointment.objects.create(
            client=user,
            service=selected_service,
            appointment_date=appointment_datetime,
        )

        # Отправка подтверждения
        bot.send_message(
            message.chat.id,
            f"Вы успешно записаны на приём!\n\n"
            f"Дата и время: {appointment.appointment_date}\n"
            f"Услуга: {appointment.service}\n"
            f"Номер телефона: {phone_number}"
        )
        send_payment_options(message.chat.id)
    else:
        bot.send_message(message.chat.id,
                         "Выбранная услуга не найдена. Пожалуйста, выберите услугу из предложенного списка.")


# ------------

def send_payment_options(chat_id):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    cash_option = types.KeyboardButton("Оплата наличными")
    yandex_kassa_option = types.KeyboardButton("Оплата онлайн через ЮKassa")

    markup.add(cash_option, yandex_kassa_option)

    bot.send_message(chat_id, "Выберите способ оплаты:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Оплата наличными")
def handle_cash_payment(message):
    bot.send_message(message.chat.id, "Вы выбрали оплату наличными. Ждем вас в офисе, до встречи!")


@bot.message_handler(func=lambda message: message.text == "Оплата онлайн через ЮKassa")
def handle_yandex_kassa_payment(message):
    # В этом месте вы можете добавить логику для интеграции с ЮKassa и создания платежа
    # После успешной оплаты, отправьте подтверждающее сообщение

    bot.send_message(message.chat.id,
                     "Вы выбрали оплату онлайн через ЮKassa. Пожалуйста, следуйте инструкциям для оплаты.")
