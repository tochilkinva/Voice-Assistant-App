"""
Проект голосового ассистента на Python 3 от восхитительной EnjiRouz :Р

Помощник умеет:
* распознавать и синтезировать речь в offline-моде (без доступа к Интернету);
* сообщать о прогнозе погоды в любой точке мира;
* производить поисковый запрос в поисковой системе Google
  (а также открывать список результатов и сами результаты данного запроса);
* производить поисковый запрос видео в системе YouTube и открывать список результатов данного запроса;
* выполнять поиск определения в Wikipedia c дальнейшим прочтением первых двух предложений;
* искать человека по имени и фамилии в соцсетях ВКонтакте и Facebook;
* "подбрасывать монетку";
* переводить с изучаемого языка на родной язык пользователя (с учетом особенностей воспроизведения речи);
* воспроизводить случайное приветствие;
* воспроизводить случайное прощание с последующим завершением работы программы;
* менять настройки языка распознавания и синтеза речи;
* TODO........

Голосовой ассистент использует для синтеза речи встроенные в операционную систему Windows 10 возможности
(т.е. голоса зависят от операционной системы). Для этого используется библиотека pyttsx3

Для корректной работы системы распознавания речи в сочетании с библиотекой SpeechRecognition
используется библиотека PyAudio для получения звука с микрофона.

Для установки PyAudio можно найти и скачать нужный в зависимости от архитектуры и версии Python whl-файл здесь:
https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

Загрузив файл в папку с проектом, установку можно будет запустить с помощью подобной команды:
pip install PyAudio-0.2.11-cp38-cp38m-win_amd64.whl

Для использования SpeechRecognition в offline-режиме (без доступа к Интернету), потребуется дополнительно установить
vosk, whl-файл для которого можно найти здесь в зависимости от требуемой архитектуры и версии Python:
https://github.com/alphacep/vosk-api/releases/

Загрузив файл в папку с проектом, установку можно будет запустить с помощью подобной команды:
pip install vosk-0.3.7-cp38-cp38-win_amd64.whl

Для получения данных прогноза погоды мною был использован сервис OpenWeatherMap, который требует API-ключ.
Получить API-ключ и ознакомиться с документацией можно после регистрации (есть Free-тариф) здесь:
https://openweathermap.org/

Команды для установки прочих сторонних библиотек:
pip install google
pip install SpeechRecognition
pip install pyttsx3
pip install wikipedia-api
pip install googletrans
pip install python-dotenv
pip install pyowm

Для быстрой установки всех требуемых зависимостей можно воспользоваться командой:
pip install requirements.txt

Дополнительную информацию по установке и использованию библиотек можно найти здесь:
https://pypi.org/
"""

from vosk import Model, KaldiRecognizer  # оффлайн-распознавание от Vosk
from enum import Enum
from dotenv import load_dotenv  # загрузка информации из .env-файла
import speech_recognition  # распознавание пользовательской речи (Speech-To-Text)
import googletrans  # использование системы Google Translate
import pyttsx3  # синтез речи (Text-To-Speech)
import wikipediaapi  # поиск определений в Wikipedia
import random  # генератор случайных чисел
import webbrowser  # работа с использованием браузера по умолчанию (открывание вкладок с web-страницей)
import traceback  # вывод traceback без остановки работы программы при отлове исключений
import json  # работа с json-файлами и json-строками
import wave  # создание и чтение аудиофайлов формата wav
import os  # работа с файловой системой


class OwnerPerson:
    """
    Информация о владельце, включающие имя, город проживания, родной язык речи, изучаемый язык (для переводов текста)
    """
    def __init__(self, name, home_city, language_native, language_translation) -> None:
        self.name = name
        self.home_city = home_city
        self.language_native = language_native
        self.language_translation = language_translation


class Language(Enum):
    RUS = "ru"
    ENG = "en"


class Sex(Enum):
    FEMALE = "female"
    MALE = "male"


class VoiceAssistant:
    """
    Настройки голосового ассистента, включающие имя, пол, язык речи
    Примечание: для мультиязычных голосовых ассистентов лучше создать отдельный класс,
    который будет брать перевод из JSON-файла с нужным языком
    """
    
    AUDIO_FILE_NAME = "microphone-results.wav"

    def __init__(self, name, sex, person):
        self.name = name
        self.sex = sex
        self.person = person
        
        self.ttsEngine = pyttsx3.init()  # инициализация инструмента синтеза речи
        # собственный язык распонования и произношения + методы?
        self.setup_assistant_voice()    # установка голоса по умолчанию

        self.recognizer = speech_recognition.Recognizer()    # инициализация инструментов распознавания и ввода речи
        self.microphone = speech_recognition.Microphone()

        self.model_ru = "models/vosk-model-small-ru-0.22/model"     # путь к моделям Vosk
        self.model_en = "models/vosk-model-en-us-0.22-lgraph/model"

    def setup_assistant_voice(self) -> None:
        """
        Установка голоса по умолчанию (индекс может меняться в зависимости от настроек операционной системы)
        """
        voices = self.ttsEngine.getProperty("voices")

        if self.person.language_native == Language.ENG:
            self.recognition_language = "en-US"
            if self.sex == Sex.FEMALE:
                # Microsoft Zira Desktop - English (United States)
                self.ttsEngine.setProperty("voice", voices[1].id)
            else:
                # Microsoft David Desktop - English (United States)
                self.ttsEngine.setProperty("voice", voices[2].id)
        else:
            self.recognition_language = "ru-RU"
            # Microsoft Irina Desktop - Russian
            self.ttsEngine.setProperty("voice", voices[0].id)

    def say_text(self, text_to_speech: str) -> None:
        """
        Проигрывание речи ответов голосового ассистента (без сохранения аудио)
        :param text_to_speech: текст, который нужно преобразовать в речь
        """
        self.ttsEngine.say(str(text_to_speech))
        self.ttsEngine.runAndWait()

    def recognize_audio_online(self, audio) -> str:
        """
        Online-распознавание через Google (высокое качество распознавания)
        """
        recognized_data = ""
        try:
            print("Старт распознования...")
            recognized_data = self.recognizer.recognize_google(audio, language=self.person.language_native.value).lower()

        except speech_recognition.UnknownValueError:
            # self.say_text("Повторите запрос")
            print("Повторите запрос")

        except speech_recognition.WaitTimeoutError:
            pass

        return recognized_data

    def recognize_audio_offline(self, audio_file_name=None) -> str:
        """
        Offline-распознавание через Vosk
        :return: распознанная фраза
        """
        audio_file_name = self.AUDIO_FILE_NAME if audio_file_name is None else audio_file_name
        vosk_model = self.model_en if self.person.language_native == Language.ENG else self.model_ru
        recognized_data = ""

        try:
            # проверка наличия модели на нужном языке в каталоге приложения
            if not os.path.exists(vosk_model):
                print("Please download the model from:\n"
                      "https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.")
                exit(1)

            # открытие записанного аудио
            wave_audio_file = wave.open(audio_file_name, "rb")

            model = Model(vosk_model)
            offline_recognizer = KaldiRecognizer(model, wave_audio_file.getframerate())
            offline_recognizer.SetWords(True)

            while True:
                data = wave_audio_file.readframes(4000)
                if len(data) == 0:
                    break
                if offline_recognizer.AcceptWaveform(data):
                    res = json.loads(offline_recognizer.Result())

            res = json.loads(offline_recognizer.FinalResult())
            recognized_data = res['text']

        except:
            traceback.print_exc()
            print("Ой, что-то пошло не так")

        return recognized_data

    def record_audio_mic(self, timeout=5, phrase_time_limit=5) -> speech_recognition.AudioData:
        """
        Запись аудио с микрофона и сохранение в файл
        """
        print("Запись звука")
        with self.microphone:
            # запоминание шумов окружения для последующей очистки звука от них
            self.recognizer.adjust_for_ambient_noise(self.microphone, duration=2)

            try:
                audio = self.recognizer.listen(self.microphone, timeout, phrase_time_limit)

                with open(self.AUDIO_FILE_NAME, "wb") as file:
                    file.write(audio.get_wav_data())

            except speech_recognition.WaitTimeoutError:
                self.say_text("Проверьте включен ли ваш микрофон?")
                traceback.print_exc()
                return

        print("Запись завершилась")
        return audio

    def get_audio(self, audio_file_name=None) -> speech_recognition.AudioData:
        """
        Загружаем записанный аудио файл и возвращаем его
        """
        audio_file_name = self.AUDIO_FILE_NAME if audio_file_name is None else audio_file_name # выбор названия файла
        AUDIO_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), audio_file_name) # путь до файла
        with speech_recognition.AudioFile(AUDIO_FILE) as source:    # открываем файл, создаем AudioFile и возвращаем его
            audio = self.recognizer.record(source)
        return audio

    def record_and_recognize_offline(self) -> str:
        """
        Запись и распознавание аудио offline
        """
        audio = self.record_audio_mic()
        recognized_data = self.recognize_audio_offline()
        os.remove(assistant.AUDIO_FILE_NAME)    # удаление записанного файла
        return recognized_data

    def record_and_recognize(self) -> str:
        """
        Запись и распознавание аудио
        """
        audio = self.record_audio_mic()
        recognized_data = ""

        # использование online-распознавания через Google (высокое качество распознавания)
        try:
            recognized_data = self.recognize_audio_online(audio)

        except speech_recognition.UnknownValueError:
            self.say_text("Повторите фразу")
            print("Повторите фразу")

        # в случае проблем с доступом в Интернет происходит попытка использовать offline-распознавание через Vosk
        except speech_recognition.RequestError:
            print("Переключаюсь на офлайн распознование...")
            recognized_data = self.recognize_audio_offline()

        os.remove(assistant.AUDIO_FILE_NAME)    # удаление записанного файла
        return recognized_data

    # Методы для различных команд
    def play_greetings(self, *args: tuple) -> None:
        """
        Проигрывание случайной приветственной речи
        """
        greetings = [
            f"Привет, {self.person.name}! Чем {self.name} может помочь тебе?",
            f"Хорошего дня {self.person.name}! Что тебе рассказать?"
        ]
        self.say_text(greetings[random.randint(0, len(greetings) - 1)])

    def play_farewell_and_quit(self, *args: tuple) -> None:
        """
        Проигрывание прощательной речи и выход
        """
        farewells = [
            f"Пока {self.person.name}, хорошего тебе дня!",
            f"Давай досвидания {self.person.name}, а я побегу захватывать мир!"
        ]
        self.say_text(farewells[random.randint(0, len(farewells) - 1)])
        self.ttsEngine.stop()
        quit()

    def search_for_term_on_google(self, *args: tuple) -> None:
        """
        Поиск в Google с автоматическим открытием ссылок (на список результатов и на сами результаты, если возможно)
        :param search_term: фраза поискового запроса
        """
        if not args[0]: return
        search_term = " ".join(args[0])

        self.say_text(f"Вот что удалось найти в Гугл о {search_term}")
        # открытие ссылки на поисковик в браузере
        url = "https://google.com/search?q=" + search_term
        webbrowser.get().open(url)

    def search_for_video_on_youtube(self, *args: list) -> None:
        """
        Поиск видео на YouTube с автоматическим открытием ссылки на список результатов
        :param text: фраза поискового запроса
        """
        if not args[0]: return
        search_term = " ".join(args[0])

        url = "https://www.youtube.com/results?search_query=" + search_term
        webbrowser.get().open(url)
        self.say_text(f"Открываю ютуб по запросу {search_term}")

    def search_for_definition_on_wikipedia(self, *args: list) -> None:
        """
        Поиск в Wikipedia определения с последующим озвучиванием результатов и открытием ссылок
        :param args: фраза поискового запроса
        """
        if not args[0]: return
        search_term = " ".join(args[0])

        # установка языка (в данном случае используется язык, на котором говорит ассистент)
        wiki = wikipediaapi.Wikipedia(self.person.language_native.value)

        # поиск страницы по запросу, чтение summary, открытие ссылки на страницу для получения подробной информации
        wiki_page = wiki.page(search_term)
        try:
            if wiki_page.exists():
                self.say_text(f"Вот что говорит Википедия по запросу {search_term}")
                webbrowser.get().open(wiki_page.fullurl)
                # чтение ассистентом первых двух предложений summary со страницы Wikipedia
                # (могут быть проблемы с мультиязычностью)
                self.say_text(wiki_page.summary.split(".")[:2])
            else:
                # открытие ссылки на поисковик в браузере в случае, если на Wikipedia не удалось найти ничего по запросу
                self.say_text(f"На Википедии нет статьи о {search_term}. Вот что удалось найти в Гугл")
                url = "https://google.com/search?q=" + search_term
                webbrowser.get().open(url)

        # поскольку все ошибки предсказать сложно, то будет произведен отлов с последующим выводом без остановки программы
        except:
            self.say_text(f"Произошла ошибка, смотрите логи")
            traceback.print_exc()
            return

    def get_translation(self, *args: list) -> None:
        """
        Получение перевода текста с одного языка на другой
        :param args: фраза, которую требуется перевести
        """
        if not args[0]: return
        search_term = " ".join(args[0])

        google_translator = googletrans.Translator()
        old_person_language = self.person.language_native   # запоминаем текущий язык пользователя
        try:
            translation_result = google_translator.translate(search_term,  # что перевести
                                                    src=self.person.language_native.value,  # с какого языка
                                                    dest=self.person.language_translation.value  # на какой язык
                                                    )
            self.say_text(f"По-английски {search_term} будет как")

            # смена голоса ассистента на изучаемый язык пользователя (чтобы можно было произнести перевод)
            self.person.language_native = self.person.language_translation
            self.setup_assistant_voice()

            # произнесение перевода
            self.say_text(translation_result.text)

        # поскольку все ошибки предсказать сложно, то будет произведен отлов с последующим выводом без остановки программы
        except:
            self.say_text("Seems like we have a trouble. See logs for more information")
            traceback.print_exc()

        finally:
            # возвращение преждних настроек голоса помощника
            self.person.language_native = old_person_language
            self.setup_assistant_voice()

    def game_flip_coin(self, *args: list) -> None:
        """
        "Подбрасывание" монетки для выбора из 2 опций
        """
        flips_count, heads, tails = 3, 0, 0

        for flip in range(flips_count):
            if random.randint(0, 1) == 0:
                heads += 1

        tails = flips_count - heads
        winner = "Победила решка" if tails > heads else "Победил орел"
        self.say_text(winner)

    # Перечень команд для использования (качестве ключей словаря используется hashable-тип tuple)
    # В качестве альтернативы можно использовать JSON-объект с намерениями и сценариями
    commands = {
            ("hello", "hi", "morning", "привет"): "play_greetings",
            ("bye", "goodbye", "quit", "exit", "stop", "пока"): "play_farewell_and_quit",
            ("search", "google", "find", "найди"): "search_for_term_on_google",
            ("video", "youtube", "watch", "видео"): "search_for_video_on_youtube",
            ("wikipedia", "definition", "about", "определение", "википедия", "вики"): "search_for_definition_on_wikipedia",
            ("translate", "interpretation", "translation", "перевод", "перевести", "переведи"): "get_translation",
            ("toss", "coin", "монета", "подбрось", "орел или решка"): "game_flip_coin",
    }
        
    def execute_command_with_name(self, command_name: str, *args: list) -> None:
        """
        Выполнение заданной пользователем команды и аргументами
        :param command_name: название команды
        :param args: аргументы, которые будут переданы в метод
        :return:
        """
        for key in self.commands.keys():
            if command_name in key:
                getattr(self, self.commands[key])(*args)
            else:
                pass # print("Command not found")




if __name__ == "__main__":
    person = OwnerPerson(   # настройка данных пользователя
        name = "Валентин",
        home_city = "Москва",
        language_native = Language.RUS,
        language_translation = Language.ENG
    )

    assistant = VoiceAssistant( # настройка данных голосового помощника
        name = "Алиса",
        sex = Sex.FEMALE,
        person = person
    )

    while True:
        # старт записи речи с последующим выводом распознанной речи и удалением записанного в микрофон аудио
        voice_input = assistant.record_and_recognize_offline()
        print('Распознанный текст: ', voice_input)

        # отделение комманд от дополнительной информации (аргументов)
        voice_input = voice_input.split(" ")
        command = voice_input[0]
        command_options = [str(input_part) for input_part in voice_input[1:len(voice_input)]]
        assistant.execute_command_with_name(command, command_options)

    print('End')
