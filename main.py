from telebot import *
import sqlite3

bot = TeleBot('TOKENBOT')


day, lesson_name, office, teacher, day_schedule = None, None, None, None, None


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,f'Привет {message.from_user.first_name}!')

@bot.message_handler(commands=['add_lesson'])
def add_lesson(message):
    conn = sqlite3.connect('schedule.sql')
    cur = conn.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS lessons (id int auto_increment primary key, day varchar(50), lesson_name varchar(50), office varchar(50), teacher varchar(50))')
    conn.commit()
    cur.close()
    conn.close()

    bot.send_message(message.chat.id, 'Введите день недели')
    bot.register_next_step_handler(message, day_name)


def day_name (message):
    global day
    day = message.text.strip()

    bot.send_message(message.chat.id, 'Введите предметы этого дня, в таком виде:\nПредмет\nПредмет\n...\nили в строчку:\nПредмет предмет предмет...\n')
    bot.register_next_step_handler(message, lesson_names)


def lesson_names(message):
    global lesson_name
    lesson_name = message.text.strip()

    bot.send_message(message.chat.id, 'Введите кабинеты для введенных уроков')
    bot.register_next_step_handler(message, office_num)


def office_num(message):
    global office
    office = message.text.strip()

    bot.send_message(message.chat.id, 'Введите ФИО учителей')
    bot.register_next_step_handler(message, teacher_name)


def teacher_name(message):
    global teacher
    teacher = message.text.strip()

    conn = sqlite3.connect('schedule.sql')
    cur = conn.cursor()

    cur.execute('INSERT INTO lessons (day, lesson_name, office, teacher) VALUES ("%s","%s","%s","%s")' % (day, lesson_name, office, teacher))
    conn.commit()
    cur.close()
    conn.close()

    markup_lessons = types.InlineKeyboardMarkup()
    markup_lessons.add(types.InlineKeyboardButton('Твое распиание', callback_data='lessons'))
    bot.reply_to(message, 'Расписание составлено', reply_markup=markup_lessons)


@bot.callback_query_handler(func=lambda call: call.data == 'lessons')
def callback_lesson(call):
    conn = sqlite3.connect('schedule.sql')
    cur = conn.cursor()
    cur.execute('SELECT * FROM lessons')
    lessons = cur.fetchall()

    information = format_schedule(lessons)
    cur.close()
    conn.close()
    bot.send_message(call.message.chat.id, information)


def format_schedule(lessons):
    if not lessons:
        return 'Уроков нет!'

    info = ''
    for lesson in lessons:
        day, lesson_names, offices, teachers = lesson[1], lesson[2].split(), lesson[3].split(), lesson[4].split()
        info += f'{day}\n'
        for i in range(len(lesson_names)):
            if lesson_names[i] != '':
                info += f'\t\t{i + 1} урок: {lesson_names[i]} {offices[i]} {teachers[i]}\n'
    return info or 'Уроков нет!'


@bot.message_handler(commands=['show_schedule'])
def show_schedule(message):
    bot.send_message(message.chat.id, 'Введите день недели, расписание которого вы хотите узнать:')
    bot.register_next_step_handler(message, get_schedule_for_day)


def get_schedule_for_day(message):
    day = message.text.strip()
    conn = sqlite3.connect('schedule.sql')
    cur = conn.cursor()
    cur.execute('SELECT lesson_name, office, teacher FROM lessons WHERE day = ?', (day,))
    lessons = cur.fetchall()
    cur.close()
    conn.close()

    if lessons:
        information = ''
        for index, (lesson_name, office, teacher) in enumerate(lessons, start=1):
            if lesson_name != '':
                lesson_parts = lesson_name.split()
                office_parts = office.split()
                teacher_parts = teacher.split()
                num_lessons = min(len(lesson_parts), len(office_parts), len(teacher_parts))

                information += f'{day}\n'
                for i in range(num_lessons):
                    information += f'\t\t{i + 1} урок: {lesson_parts[i]} {office_parts[i]} {teacher_parts[i]}\n'

    else:
        information = f'На {day} нет уроков.'

    bot.send_message(message.chat.id, information)


@bot.message_handler(commands=['help'])
def com_help(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('ТГ Разработчика', url = 'https://t.me/jeeerrkk'))
    bot.reply_to(message, 'Если возникли вопросы, писать разработчику ;)', reply_markup = markup)


@bot.message_handler()
def incorrect_message(message):
    if message.text.lower() != '/start' or message.text.lower() != '/help' or message.text.lower() != '/add_lesson' or message.text.lower() != '/show schedule':
        bot.reply_to(message, 'Неизвестная команда!\nВарианты команд:\n/start - Запуск бота;\n/help - Помощь;\n/add_lesson - Добавить занятия на день;\n/show_schedule - Показать расписание')



bot.infinity_polling()