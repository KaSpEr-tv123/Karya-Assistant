from __future__ import annotations

import os
import random
import re
import time

from PyQt5.QtWidgets import QMessageBox, QWidget
from PyQt5.QtGui import QColor, QPixmap
import discord
from googletrans import Translator
from kasperdb import db
import requests

from .types import KaryaContext, KaryaCommands, KaryaCommand

def set_settings(temperature) -> None:
    data = db.get("database/settings")
    data["temperature"] = temperature
    db.set("database/settings", data)

class CommandCompiler:
    commands = KaryaCommands()
    is_testing_mode = False

    @staticmethod
    def register_command(command_name, description="", args=""):
        """Декоратор для регистрации команды."""
        def decorator(func):
            CommandCompiler.commands.add_command(KaryaCommand(command_name, description, args, func))
            return func
        return decorator

    @staticmethod
    async def send(app: typing.Union[QWidget, KaryaContext], command_name, args, result="Выполнено", type="chat"):
        """Отправить результат команды в чат и в лог."""
        if type == "chat":
            app.chat_area.setTextColor(QColor(255, 165, 0))
            app.chat_area.append(f"Система: Вызвана команда {command_name} \nаргументы: {args}\nрезультат: {result}\n")
        else:
            embeds = app.botmsg.embeds or [] 
            embeds.append(discord.Embed(
                title="Система",
                description=f"Вызвана команда {command_name} \nаргументы: {args}\nрезультат: {result}\n",
                color=discord.Color.orange()
            ))
            await app.edit(embeds=embeds)
        with open("database/chat.log", "a", encoding="utf-8") as f:
            f.write(f"\nСистема: 'Вызвана команда {command_name} с аргументами: {args}. результат: {result}\n'")  # Логируем команду

    @staticmethod
    async def sendimg(app: typing.Union[QWidget, KaryaContext], image_source, description="Изображение", type="chat"):
        """
        Отправляет изображение в чат приложения.
        
        :param app: Экземпляр приложения.
        :param image_source: Путь или ссылка на изображение.
        :param description: Описание изображения (по умолчанию "Изображение").
        """
        try:
            if type == "chat":
                app.chat_area.setTextColor(QColor(255, 165, 0))
                if image_source.startswith("http://") or image_source.startswith("https://"):
                    response = requests.get(image_source, stream=True)
                    if response.status_code == 200:
                        temp_file = f"temp_image_{int(time.time())}_{random.randint(1000, 9999)}.jpg"
                        with open(temp_file, "wb") as f:
                            f.write(response.content)
                        image_path = temp_file
                    else:
                        app.chat_area.append(f"Ошибка: Не удалось загрузить изображение по ссылке {image_source}")
                        return
                else:
                    # Если это не ссылка, предполагаем, что это путь к файлу
                    image_path = image_source

                # Загружаем изображение в QPixmap
                pixmap = QPixmap(image_path)
                if pixmap.isNull():
                    app.chat_area.append(f"Ошибка: Не удалось загрузить изображение по пути {image_path}")
                    return

                original_width = "1000"
                original_height = "1000"

                # Отображаем изображение в чате
                app.chat_area.append(f"Система: Изображение отправлено. Описание: {description}")
                app.chat_area.insertHtml(f'<br><img src="{image_path}" width={original_width} height={original_height}><br>')

                # Логируем изображение
                with open("database/chat.log", "a", encoding="utf-8") as f:
                    f.write(f"\nСистема: Изображение добавлено. Описание: {description}, Источник: {image_source}\n")

                if os.path.exists(image_path):
                    os.remove(image_path)
            else:
                emb = discord.Embed(title="Изображение", description=description, color=discord.Color.orange())
                emb.set_image(url=image_source)
                await app.channel.send(embed=emb)
                with open("database/chat.log", "a", encoding="utf-8") as f:
                    f.write(f"\nСистема: Изображение добавлено. Описание: {description}, Источник: {image_source}\n")

        except Exception as e:
            if type == "chat":
                app.chat_area.setTextColor(QColor(255, 0, 0))
                app.chat_area.append(f"Ошибка при отправке изображения: {e}")
            else:
                await app.channel.send(embed=discord.Embed(title="Ошибка", description=f"Произошла ошибка при отправке изображения: {e}", color=0xff0000))

    @staticmethod
    async def compile(user_input, app, type="chat"):
        """Обрабатываем команду в запросе."""
        matches = re.findall(r"#(\w+)\((.*?)\)", user_input)

        if matches:
            for command_name, args in matches:
                if not CommandCompiler.is_testing_mode:
                    try:
                        command = CommandCompiler.commands.get_command(command_name)
                        if command:
                            await command.function(args, app, type)
                    except Exception as e:
                        await CommandCompiler.send(app, command_name, args, f"Произошла ошибка: {e}, возможно были не введены аргументы", type)
                else:
                    if command_name == "setTestingMode" or command_name == "getTestingMode":
                        command = CommandCompiler.commands.get_command(command_name)
                        if command:
                            await command.function(args, app, type)
                    else:
                        await CommandCompiler.send(app, command_name, args, "Не выполнена", type)

@CommandCompiler.register_command("createMessagebox", description="Создает окно сообщения, а в дискорде эмбед", args="текст")
async def create_messagebox(args, app, type):
    if type == "chat":
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(args)
        msg.setWindowTitle("Сообщение от Кари в системе")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        await CommandCompiler.send(app, "createMessagebox", args)
    else:
        await app.channel.send(embed=discord.Embed(title="Особое Сообщение от Кари в системе", description=args, color=0x00ff00))
        await CommandCompiler.send(app, "createMessagebox", args, type="discord")

@CommandCompiler.register_command("setMode", description="Устанавливает режим работы, 1 - точный, 2 - обычный, 3 - креативный", args="цифра")
async def set_mode(mode, app, type):
    if mode == "1":
        set_settings(0.1)
    elif mode == "3":
        set_settings(0.9)
    elif mode == "2":
        set_settings(0.7)
    
    await CommandCompiler.send(app,"setMode", mode, type=type)  # Используем send для записи и отображения

@CommandCompiler.register_command("getDate", description="Возвращает текущую дату и время", args="")
async def get_date(args, app, type):
    result = time.strftime('%Y-%m-%d %H:%M:%S')
    
    await CommandCompiler.send(app, "getDate", args, result, type)  # Используем send для записи и отображения

@CommandCompiler.register_command("clearChat", description="Очищает историю чата и память", args="")
async def clear_chat(args, app, type):
    with open("database/chat.log", "w") as log_file:
        log_file.truncate(0)  # Очищаем файл, делая его пустым
    if type == "chat":
        app.chat_area.clear()
    await CommandCompiler.send(app, "clearChat", args, type=type)  # Используем send для записи и отображения


@CommandCompiler.register_command("setTestingMode", description="Включает режим тестирования, при включенном режиме команды не будут выполняться, 1 - включить, 0 - выключить", args="цифра")
async def set_testing_mode(args, app, type):
    # Проверяем, что аргумент является допустимым числом (например, 1)
    try:
        # Преобразуем строку в число
        mode = int(args)
        if mode == 1:
            CommandCompiler.is_testing_mode = True
            result = "Режим тестирования включен."
        else:
            CommandCompiler.is_testing_mode = False
            result = "Режим тестирования отключен."
    except ValueError:
        result = "Ошибка: некорректный аргумент для режима тестирования."
    
    await CommandCompiler.send(app, "setTestingMode", args, result, type)


@CommandCompiler.register_command("getTestingMode", description="Возвращает состояние режима тестирования", args="")
async def get_testing_mode(args, app, type):
    if CommandCompiler.is_testing_mode:
        result = "Режим тестирования включен."
    else:
        result = "Режим тестирования отключен."

    await CommandCompiler.send(app, "getTestingMode", args, result, type)

@CommandCompiler.register_command("translator", description="Переводит текст", args="текст;язык")
async def translator(args, app, type):
    translator = Translator()
    text, lang = [arg.strip().strip('"') for arg in args.split(";")]
    result = await translator.translate(text, dest=lang)
    await CommandCompiler.send(app, "translator", args, result.text, type)

@CommandCompiler.register_command("search", description="Поиск в Google", args="текст;режим")
async def search(args, app, type):
    api_key = "" # Ваш апи ключ из гугл клауд консоли
    search_engine_id = ""   # Айди поисковой системы

    query, mode = [arg.strip().strip('"') for arg in args.split(";")]
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={search_engine_id}"

    try:
        response = requests.get(url)
        response.raise_for_status() 

        data = response.json()

        if 'items' in data:
            if mode == "1":
                result = data['items'][0]['link']
            elif mode == "2":
                result = data['items'][0]['title']
            elif mode == "3":
                result = data['items'][0]['snippet']
        else:
            result = "Нет результатов для данного запроса."

    except requests.exceptions.RequestException as e:
        result = f"Ошибка при запросе к API: {e}" 
    except Exception as e:
        result = f"Произошла ошибка: {e}" 

    await CommandCompiler.send(app, "search", args, result, type)

@CommandCompiler.register_command("getWeather", description="Получение и отправка погоды", args="город")
async def weather(args, app, type):
    api_key = ""  # Вставьте сюда ваш ключ API OpenWeatherMap
    city = args 
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"  # Запрос с единицами в Цельсиях и на русском языке

    try:
        response = requests.get(url)
        response.raise_for_status()  

        data = response.json()

        if data['cod'] == 200:
    
            city_name = data['name']
            temperature = data['main']['temp']
            weather_description = data['weather'][0]['description']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']

            result = (f"Погода в {city_name}:\n"
                      f"Температура: {temperature}°C\n"
                      f"Описание: {weather_description}\n"
                      f"Влажность: {humidity}%\n"
                      f"Скорость ветра: {wind_speed} м/с")

        else:
            result = "Не удалось получить данные о погоде для этого города."

    except requests.exceptions.RequestException as e:
        result = f"Ошибка при запросе погоды: {e}"

    except Exception as e:
        result = f"Произошла ошибка: {e}"

    await CommandCompiler.send(app, "getWeather", args, result, type)

@CommandCompiler.register_command("memorySave", description="Сохраняет данные в память навсегда, максимум 50 строк.", args="текст")
async def memory_save(args, app, type):
    with open("database/memory.txt", "r+", encoding="utf-8") as f:
        try:
            lines = f.readlines()
            if len(lines) < 50:
                f.seek(0, 2)
                f.write(args + "\n")
                result = "Сохранено в память."
            else:
                result = "Память заполнена. Сохранение невозможно."
        except Exception as e:
            result = f"Произошла ошибка: {e}, но данные сохранены"
            f.seek(0, 2)
            f.write(args + "\n")

    await CommandCompiler.send(app, "memorySave", args, result, type)

@CommandCompiler.register_command("createQRCode")
async def create_qr_code(args, app, type):
    response = requests.get("https://api.qrserver.com/v1/create-qr-code/?data="+args)
    response.raise_for_status()
    result = response.json()["url"]
    await CommandCompiler.sendimg(app, result, args, type)

@CommandCompiler.register_command("getAnimeImage", description="Возвращает картинку аниме, типы: milf, neko, trap, blowjob", args="тип")
async def get_anime_image(args, app, type):
    response = requests.get("https://api.waifu.pics/nsfw/"+args)
    response.raise_for_status()
    result = response.json()["url"]

    await CommandCompiler.sendimg(app, result, args, type)

@CommandCompiler.register_command("createRole", description="Создает роль, пример указания прав: manage_messages:True, manage_channels:False", args="цвет hex;название;права")
async def create_role(args, app: typing.Union[QWidget, KaryaContext], type):
    if type == "chat":
        return await CommandCompiler.send(app, "createRole", args, "Вы не можете использовать эту команду в чате кроме дискорда", type)

    try:
        parts = [arg.strip() for arg in args.split(";")]

        if len(parts) != 3:
            raise ValueError("Не хватает аргументов. Требуется: цвет, название и права.")

        color, name, permissions = parts

        permissions_dict = {}
        for permission in permissions.split(","):
            perm_parts = permission.split(":")
            if len(perm_parts) == 2:
                key = perm_parts[0].strip()
                value = perm_parts[1].strip().lower() == "true"  
                permissions_dict[key] = value

        permissions_obj = discord.Permissions(**permissions_dict)

        color_int = int(color.lstrip('#'), 16) if color.startswith('#') else int(color, 16)

        role = await app.guild.create_role(
            name=name,
            colour=color_int,
            permissions=permissions_obj
        )

        await CommandCompiler.send(app, "createRole", args, f"Роль успешно создана. role ID: {role.id}", type)
    except ValueError as e:
        await CommandCompiler.send(app, "createRole", args, f"Ошибка в аргументах: {str(e)}", type)
    except discord.errors.Forbidden as e:
        await CommandCompiler.send(app, "createRole", args, "Нет прав для создания роли.", type)
    except Exception as e:
        await CommandCompiler.send(app, "createRole", args, f"Произошла ошибка: {str(e)}", type)

@CommandCompiler.register_command("deleteRole", description="Удаляет роль", args="ID роли")
async def delete_role(args, app: typing.Union[QWidget, KaryaContext], type):
    if type == "chat":
        return await CommandCompiler.send(app, "deleteRole", args, "Вы не можете использовать эту команду в чате кроме дискорда", type)
    
    try:
        role_id = args.strip()
        role = discord.utils.get(app.guild.roles, id=int(role_id))
        if role is not None:
            await role.delete()
            await CommandCompiler.send(app, "deleteRole", args, "Роль успешно удалена.", type)
        else:
            await CommandCompiler.send(app, "deleteRole", args, "Роль не найдена.", type)
    except Exception as e:
        await CommandCompiler.send(app, "deleteRole", args, f"Произошла ошибка: {e}", type)

@CommandCompiler.register_command("createChannel", description="Создает канал", args="тип;название")
async def create_channel(args, app: typing.Union[QWidget, KaryaContext], type):
    if type == "chat":
        return await CommandCompiler.send(app, "createChannel", args, "Вы не можете использовать эту команду в чате кроме дискорда", type)
    
    try:
        channel_type, name = [arg.strip() for arg in args.split(";")]
        if channel_type == "text":
            channel = await app.guild.create_text_channel(name)
        elif channel_type == "voice":
            channel = await app.guild.create_voice_channel(name)
        elif channel_type == "stage":
            channel = await app.guild.create_stage_channel(name)
        else:
            return await CommandCompiler.send(app, "createChannel", args, "Неверный тип канала. Используйте 'text' или 'voice'.", type)
        
        await CommandCompiler.send(app, "createChannel", args, f"Канал {name}(`{channel.id}`) успешно создан!", type)
    except Exception as e:
        await CommandCompiler.send(app, "createChannel", args, f"Произошла ошибка: {e}", type)

@CommandCompiler.register_command("deleteChannel", description="Удаляет канал", args="ID канала")
async def delete_channel(args, app: typing.Union[QWidget, KaryaContext], type):
    if type == "chat":
        return await CommandCompiler.send(app, "deleteChannel", args, "Вы не можете использовать эту команду в чате кроме дискорда", type)
    
    try:
        id = args.strip()
        channel = discord.utils.get(app.guild.channels, id=int(id))
        await channel.delete()
        
        await CommandCompiler.send(app, "deleteChannel", args, f"Канал {id} успешно удален!", type)
    except Exception as e:
        await CommandCompiler.send(app, "deleteChannel", args, f"Произошла ошибка: {e}", type)

@CommandCompiler.register_command("banUser", description="Забанить пользователя", args="ID пользователя;причина")
async def ban_user(args, app: typing.Union[QWidget, KaryaContext], type):
    if type == "chat":
        return await CommandCompiler.send(app, "banUser", args, "Вы не можете использовать эту команду в чате кроме дискорда", type)
    
    try:
        user_id, reason = [arg.strip() for arg in args.split(";")]
        user = await app.guild.fetch_member(int(user_id))
        
        await user.ban(reason=reason)
        await CommandCompiler.send(app, "banUser", args, f"Пользователь {user} успешно забанен по причине: {reason}", type)
    except Exception as e:
        await CommandCompiler.send(app, "banUser", args, f"Произошла ошибка: {e}", type)

@CommandCompiler.register_command("unbanUser", description="Разбанить пользователя", args="ID пользователя;причина")
async def unban_user(args, app: typing.Union[QWidget, KaryaContext], type):
    if type == "chat":
        return await CommandCompiler.send(app, "unbanUser", args, "Вы не можете использовать эту команду в чате кроме дискорда", type)
    
    try:
        user_id, reason = [arg.strip() for arg in args.split(";")]
        
        await app.guild.unban(int(user_id), reason=reason)
        await CommandCompiler.send(app, "unbanUser", args, f"Пользователь {user_id} успешно разбанен по причине: {reason}", type)
    except Exception as e:
        await CommandCompiler.send(app, "unbanUser", args, f"Произошла ошибка: {e}", type)

@CommandCompiler.register_command("deleteMessage", description="Удаляет сообщение", args="ID сообщения")
async def delete_message(args, app: typing.Union[QWidget, KaryaContext], type):
    if type == "chat":
        return await CommandCompiler.send(app, "deleteMessage", args, "Вы не можете использовать эту команду в чате кроме дискорда", type)
    
    try:
        message_id = args.strip()
        message = await app.channel.fetch_message(int(message_id))
        await message.delete()
        await CommandCompiler.send(app, "deleteMessage", args, f"Сообщение {message_id} успешно удалено.", type)
    except Exception as e:
        await CommandCompiler.send(app, "deleteMessage", args, f"Произошла ошибка: {e}", type)

@CommandCompiler.register_command("giveRole", description="Выдает роль пользователю", args="ID пользователя;ID роли")
async def assign_role(args, app: typing.Union[QWidget, KaryaContext], type):
    if type == "chat":
        return await CommandCompiler.send(app, "giveRole", args, "Вы не можете использовать эту команду в чате кроме дискорда", type)
    
    try:
        user_id, role_id = [arg.strip() for arg in args.split(";")]
        user = await app.guild.fetch_member(int(user_id))
        role = discord.utils.get(app.guild.roles, id=int(role_id))
        
        if role:
            await user.add_roles(role)
            await CommandCompiler.send(app, "giveRole", args, f"Роль {role_id} успешно назначена пользователю {user}.", type)
        else:
            await CommandCompiler.send(app, "giveRole", args, f"Роль {role_id} не найдена.", type)
    except Exception as e:
        await CommandCompiler.send(app, "giveRole", args, f"Произошла ошибка: {e}", type)

@CommandCompiler.register_command("takeRole", description="Снимает роль у пользователя", args="ID пользователя;ID роли")
async def unassign_role(args, app: typing.Union[QWidget, KaryaContext], type):
    if type == "chat":
        return await CommandCompiler.send(app, "takeRole", args, "Вы не можете использовать эту команду в чате кроме дискорда", type)
    
    try:
        user_id, role_id = [arg.strip() for arg in args.split(";")]
        user = await app.guild.fetch_member(int(user_id))
        role = discord.utils.get(app.guild.roles, id=int(role_id))
        
        if role:
            await user.remove_roles(role)
            await CommandCompiler.send(app, "takeRole", args, f"Роль {role_id} успешно снята у пользователя {user}.", type)
        else:
            await CommandCompiler.send(app, "takeRole", args, f"Роль {role_id} не найдена.", type)
    except Exception as e:
        await CommandCompiler.send(app, "takeRole", args, f"Произошла ошибка: {e}", type)

@CommandCompiler.register_command("serverInfo", description="Показывает информацию о сервере", args="")
async def server_info(args, app: typing.Union[QWidget, KaryaContext], type):
        if type == "chat":
            return await CommandCompiler.send(app, "serverInfo", args, "Вы не можете использовать эту команду в чате кроме дискорда", type)
    
        guild = app.guild
        server_name = guild.name
        server_id = guild.id
        owner = guild.owner
        member_count = guild.member_count
        created_at = guild.created_at.strftime("%Y-%m-%d %H:%M:%S")
        verification_level = guild.verification_level.name
        afk_channel = guild.afk_channel.name if guild.afk_channel else "Не задан"
        icon_url = guild.icon.url if guild.icon else "Нет иконки"
        
        # Формируем сообщение с информацией о сервере
        info_message = (
            f"**Информация о сервере**\n"
            f"Название: {server_name}\n"
            f"ID: {server_id}\n"
            f"Владелец: {owner}\n"
            f"Количество участников: {member_count}\n"
            f"Дата создания: {created_at}\n"
            f"Уровень проверки: {verification_level}\n"
            f"AFK-канал: {afk_channel}\n"
            f"Иконка: {icon_url}"
        )
        
        await CommandCompiler.send(app, "serverInfo", args, info_message, type)

@CommandCompiler.register_command("sendDiscordServerInviteLink", description="Отправляет ссылку на сервер в дискорд", args="ID сервера;ID канала или ID пользователя")
async def send_discord_server_invite_link(args, app: typing.Union[QWidget, KaryaContext], type):
    if type == "chat":
        return await CommandCompiler.send(app, "sendDiscordServerInviteLink", args, "Вы не можете использовать эту команду в чате кроме дискорда", type)
    
    try:
        guildid, channeluserid = [arg.strip() for arg in args.split(";")]
        guild = app.guild
        channel = guild.get_channel(int(channeluserid))
        guild = app.bot.get_guild(int(guildid))
        if not channel:
            channel = guild.get_member(int(channeluserid))
        invite_link = await guild.invites()
        await channel.send(invite_link[0].url)
        await CommandCompiler.send(app, "sendDiscordServerInviteLink", args, f"Ссылка на сервер отпралена", type)
    except Exception as e:
        await CommandCompiler.send(app, "sendDiscordServerInviteLink", args, f"Произошла ошибка: {e}", type)

@CommandCompiler.register_command("editRole", description="Редактирует роль, пример указания прав: manage_messages:True, manage_channels:False", args="ID роли;Новое имя;Цвет;Права")
async def edit_role(args, app: typing.Union[QWidget, KaryaContext], type):
    if type == "chat":
        return await CommandCompiler.send(app, "editRole", args, "Вы не можете использовать эту команду в чате, кроме Discord", type)

    try:
        args = [arg.strip() for arg in args.split(";")]
        
        if len(args) < 1:
            raise ValueError("Не передан ID роли.")
        
        role_id = int(args[0])   # ID роли
        new_name = None          # Имя роли (если передано)
        color = None             # Цвет роли (если передан)
        permissions = {}         # Права (если будут переданы)

        if len(args) > 1 and args[1]:
            new_name = args[1]   
        
        if len(args) > 2 and args[2]:
            if args[2].startswith("#"):
                color = int(args[2].lstrip("#"), 16) 
            else:
                raise ValueError("Цвет должен быть в формате hex, например, #FF5733.")
        
        if len(args) > 3 and args[3]:
            perms_args = args[3].split(",") 
            for perm in perms_args:
                perm_name, perm_value = perm.split(":")
                permissions[perm_name.strip()] = perm_value.strip().lower() == "true"
        
        role = app.guild.get_role(role_id)
        
        if not role:
            raise ValueError("Роль с таким ID не найдена.")
        
        if new_name:
            await role.edit(name=new_name)
        
        if color:
            await role.edit(colour=color)
        
        if permissions:
            await role.edit(**permissions)

        return await CommandCompiler.send(app, "editRole", args, f"Роль с ID {role_id} успешно изменена.", type)
    
    except ValueError as e:
        return await CommandCompiler.send(app, "editRole", args, f"Ошибка: {str(e)}", type)
    
    except Exception as e:
        return await CommandCompiler.send(app, "editRole", args, f"Произошла ошибка: {str(e)}", type)

@CommandCompiler.register_command("giveRoleForAll", description="Дает роль всем участникам сервера", args="ID роли")
async def give_role_for_all(args, app: typing.Union[QWidget, KaryaContext], type):
    if type == "chat":
        return await CommandCompiler.send(app, "giveRoleForAll", args, "Вы не можете использовать эту команду в чате, кроме Discord", type)

    try:
        role_id = int(args.strip())
        role = app.guild.get_role(role_id)
        if not role:
            return await CommandCompiler.send(app, "giveRoleForAll", args, f"Роль с ID {role_id} не была найдена.", type)
        for member in app.guild.members:
            await member.add_roles(role)
        return await CommandCompiler.send(app, "giveRoleForAll", args, f"Роль с ID {role_id} была успешно выдана всем участникам сервера.", type)
    except Exception as e:
        return await CommandCompiler.send(app, "giveRoleForAll", args, f"Произошла ошибка: {str(e)}", type)    

@CommandCompiler.register_command("help", description="Показывает список команд, используй это чтобы показать свои возможности, не делай это сама т.к. это может привести к спаму", args="")
async def help(args, app: typing.Union[QWidget, KaryaContext], type):
    if type == "chat":
        return await CommandCompiler.send(app, "help", args, CommandCompiler.commands.get_strcommands(), type)

    await CommandCompiler.send(app, "help", args, "\nСписок команд: \n" + CommandCompiler.commands.get_strcommands(), type)
