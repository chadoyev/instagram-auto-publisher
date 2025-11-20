from datetime import datetime, timedelta, date
import time
import shutil
from moviepy.editor import *
from instagrapi import Client
import json
import os
from PIL import Image
import random
import math
import threading
from multiprocessing import Process


class StartLoop():
    """Класс для управления циклом автопостинга (из OLD версии loopbot.py)"""
    
    def __init__(self, db, cl):
        """
        Инициализация
        
        Args:
            db: Объект базы данных
            cl: Instagram клиент
        """
        self.loopflag = False
        self.thread = None
        self.db = db
        self.cl = cl
        self.name_pablik = "Подписывайся на ..."
    
    def media_pk_cut(self, file, ask):
        """Достаёт описание из БД"""
        if ask == True:
            ppp = file.count('_')
            file = os.path.splitext(file)[0]
            file = (file.split('_')[ppp])
        try:
            baza = "SELECT media_description FROM media_descriptions WHERE media_pk = {}".format(file)
            result = self.db.cursor.execute(baza).fetchone()
            return (result[0])
        except:
            return (" ")
    
    def make_watermark(self, path, file):
        """Добавляет водяной знак на видео"""
        file_without_wm = os.path.join(path + file)
        copy = os.path.join(path + "wm_" + file)
        file_with_wm = os.path.join(path + "with_wm_" + file)
        shutil.copyfile(file_without_wm, copy)
        time.sleep(1)
        video1 = VideoFileClip(copy)
        audio = AudioFileClip(file_without_wm)
        
        # Проверяем наличие logo.png
        if os.path.exists("logo.png"):
            logo = (
                ImageClip("logo.png").set_duration(video1.duration).resize(height=150).margin(opacity=0.1).set_position((0.75, 0.8),
                                                                                                               relative=True))
            final = CompositeVideoClip([video1, logo])
        else:
            final = video1
        
        final = final.set_audio(audio)
        final.write_videofile(file_with_wm)
        video1.close()
        os.remove(copy)
        return file_with_wm, file_without_wm
    
    def remove_used(self, path, file):
        """Удаляет использованный медиафайл"""
        list_f = os.listdir(path)
        name_file = os.path.splitext(file)[0]
        for item in list_f:
            if name_file in os.path.splitext(item)[0]:
                os.remove(path + item)
    
    def remove_temp_photo(self, path, file):
        """Удаляет временное фото превью"""
        list_f = os.listdir(path)
        name_file = os.path.splitext(file)[0]
        for item in list_f:
            if name_file in os.path.splitext(item)[0]:
                if item.endswith(".jpg"):
                    os.remove(path + item)
    
    def get_old_file(self, path):
        """Выбирает самый старый файл"""
        files = os.listdir(path)
        files = [os.path.join(path, file) for file in files]
        files = [file for file in files if os.path.isfile(file)]
        file_main = min(files, key=os.path.getctime)
        return (os.path.basename(file_main))
    
    def convert_webp_to_jpeg_u(self, con):
        """Конвертирует webp в jpeg"""
        if con.endswith(".webp"):
            fi = os.path.splitext(con)[0]
            im = Image.open("photo_posts/" + con).convert("RGB")
            im.save("photo_posts/" + str(fi) + ".jpg", "jpeg")
            os.remove("photo_posts/" + con)
            return str(fi+".jpg")
        else:
            return con
    
    def upload_story_video(self):
        """Загружает видео историю"""
        file_with_wm = None
        try:
            file = self.get_old_file("storys/video/")
            file_with_wm, file_without_wm = self.make_watermark("storys/video/", file)
            converter = Process(target=self.cl.video_upload_to_story, args=(file_with_wm,))
            converter.start()
            converter.join()
            print("Загрузил видео историю: " + str(file_with_wm))
            for _ in range(10):
                try:
                    os.remove(file_with_wm)
                    os.remove(file_without_wm)
                    self.remove_temp_photo("storys/video/", "with_wm_" + file)
                    break
                except OSError:
                    time.sleep(0.1)
        except Exception as e:
            print(e)
            if file_with_wm:
                try:
                    os.remove(file_with_wm)
                    self.remove_temp_photo("storys/video/", "with_wm_" + file)
                except:
                    pass
    
    def upload_story_image(self):
        """Загружает фото историю"""
        try:
            file = self.get_old_file("storys/photo/")
            self.cl.photo_upload_to_story("storys/photo/" + file)
            print("Загрузил фото историю: " + str(file))
            for _ in range(10):
                try:
                    self.remove_used("storys/photo/", file)
                    break
                except OSError:
                    time.sleep(0.1)
        except:
            pass
    
    def upload_post_image(self):
        """Загружает фото пост"""
        try:
            file = self.get_old_file("photo_posts/")
            desc = str(self.media_pk_cut(file, True))
            self.cl.photo_upload("photo_posts/" + file, desc)
            file = self.convert_webp_to_jpeg_u(file)
            print("Загрузил фото пост: " + str(file))
            for _ in range(10):
                try:
                    self.remove_used("photo_posts/", file)
                    break
                except OSError:
                    time.sleep(0.1)
        except Exception as e:
            print(str(e))
    
    def upload_post_video(self):
        """Загружает видео пост"""
        file_with_wm = None
        try:
            file = self.get_old_file("video_posts/")
            desc = str(self.media_pk_cut(file, True))
            file_with_wm, file_without_wm = self.make_watermark("video_posts/", file)
            converter = Process(target=self.cl.video_upload, args=(file_with_wm, desc))
            converter.start()
            converter.join()
            print("Загрузил видео пост: " + str(file_with_wm))
            for _ in range(10):
                try:
                    os.remove(file_with_wm)
                    os.remove(file_without_wm)
                    self.remove_temp_photo("video_posts/", "with_wm_" + file)
                    break
                except OSError:
                    time.sleep(0.1)
        except Exception as e:
            if file_with_wm:
                try:
                    os.remove(file_with_wm)
                    self.remove_temp_photo("video_posts/", "with_wm_" + file)
                except:
                    pass
    
    def upload_album_posts(self):
        """Загружает альбомный пост"""
        try:
            folders = os.listdir("albums_posts")
            element = random.choice(folders)
            desc = str(self.media_pk_cut(element, False))
            files = os.listdir("albums_posts/" + element)
            for key, value in enumerate(files):
                files[key] = "albums_posts/" + element + "/" + value
            converter = Process(target=self.cl.album_upload, args=(files, desc))
            converter.start()
            converter.join()
            print("Загрузил альбомный пост: " + str(files))
            for _ in range(10):
                try:
                    shutil.rmtree("albums_posts/" + element)
                    break
                except OSError:
                    time.sleep(0.1)
        except:
            pass
    
    def upload_igtv(self):
        """Загружает IGTV пост"""
        file_with_wm = None
        try:
            file = self.get_old_file("video_posts/igtv/")
            desc = str(self.media_pk_cut(file, True))
            if desc == "":
                desc = self.name_pablik
            file_with_wm, file_without_wm = self.make_watermark("video_posts/igtv/", file)
            converter = Process(target=self.cl.igtv_upload, args=(file_with_wm, desc, " "))
            converter.start()
            converter.join()
            print("Загрузил IGTV пост: " + str(file_with_wm))
            for _ in range(10):
                try:
                    os.remove(file_with_wm)
                    os.remove(file_without_wm)
                    self.remove_temp_photo("video_posts/igtv/", "with_wm_" + file)
                    break
                except OSError:
                    time.sleep(0.1)
        except Exception as e:
            if file_with_wm:
                try:
                    os.remove(file_with_wm)
                    self.remove_temp_photo("video_posts/igtv/", "with_wm_" + file)
                except:
                    pass
    
    def upload_clips(self):
        """Загружает клип"""
        file_with_wm = None
        try:
            file = self.get_old_file("video_posts/clips/")
            desc = str(self.media_pk_cut(file, True))
            file_with_wm, file_without_wm = self.make_watermark("video_posts/clips/", file)
            converter = Process(target=self.cl.clip_upload, args=(file_with_wm, desc))
            converter.start()
            converter.join()
            print("Загрузил клип: " + str(file_with_wm))
            for _ in range(10):
                try:
                    os.remove(file_with_wm)
                    os.remove(file_without_wm)
                    self.remove_temp_photo("video_posts/clips/", "with_wm_" + file)
                    break
                except OSError:
                    time.sleep(0.1)
        except Exception as e:
            print(e)
            if file_with_wm:
                try:
                    os.remove(file_with_wm)
                    self.remove_temp_photo("video_posts/clips/", "with_wm_" + file)
                except:
                    pass
    
    def get_from_bd(self, column):
        """Получает значение из БД"""
        return self.db.get_setting(column)
    
    def set_to_bd(self, column, value):
        """Устанавливает значение в БД"""
        self.db.set_setting(column, value)
    
    def add_count_to_bd(self, content):
        """Увеличивает счётчик в БД"""
        old_value = self.get_from_bd(content)
        value = old_value + 1
        self.set_to_bd(content, value)
    
    def count_files(self, content):
        """Подсчитывает количество файлов определённого типа"""
        if content == "СВ":
            count_story_video = len(os.listdir("storys/video"))
            return count_story_video
        if content == "СФ":
            count_story_photo = len(os.listdir("storys/photo"))
            return count_story_photo
        if content == "ВП":
            count_post_video_temp = os.listdir("video_posts")
            co1 = 0
            for file in count_post_video_temp:
                if file.endswith(".mp4"):
                    co1 += 1
            count_post_video = co1
            return count_post_video
        if content == "ФП":
            count_post_image = len(os.listdir("photo_posts"))
            return count_post_image
        if content == "АП":
            count_albums = len(os.listdir("albums_posts"))
            return count_albums
        if content == "ИТ":
            count_igtv = len(os.listdir("video_posts/igtv"))
            return count_igtv
        if content == "К":
            count_clips = len(os.listdir("video_posts/clips"))
            return count_clips
    
    def number_get(self, chislo):
        """Вспомогательная функция"""
        if chislo == 0:
            return 0
        else:
            return chislo+1
    
    def post(self, faza, t1, t2):
        """Публикует контент для определённой фазы"""
        faza_process = faza.split("_")
        contents = self.get_from_bd(faza).split("-")
        raznica = (datetime.combine(date.min, t2) - datetime.combine(date.min, t1)).total_seconds() / 60
        count_content = len(contents)
        max_time_sleep = math.floor(raznica / count_content)
        current_position_now = self.get_from_bd("current_position_content").split("-")
        if current_position_now[0] == "0":
            a = -1
        elif current_position_now[0] == faza_process[0]:
            a = int(current_position_now[1])-1
        else:
            a = -1
        for i in range(a+1, len(contents)):
            if contents[i] == "СВ":
                if self.count_files(contents[i]) != 0:
                    self.upload_story_video()
                    self.add_count_to_bd("uploaded_video_story")
            if contents[i] == "СФ":
                if self.count_files(contents[i]) != 0:
                    self.upload_story_image()
                    self.add_count_to_bd("uploaded_photo_story")
            if contents[i] == "ВП":
                if self.count_files(contents[i]) != 0:
                    self.upload_post_video()
                    self.add_count_to_bd("uploaded_video_posts")
            if contents[i] == "ФП":
                if self.count_files(contents[i]) != 0:
                    self.upload_post_image()
                    self.add_count_to_bd("uploaded_photo_posts")
            if contents[i] == "АП":
                if self.count_files(contents[i]) != 0:
                    self.upload_album_posts()
                    self.add_count_to_bd("uploaded_album_posts")
            if contents[i] == "ИТ":
                if self.count_files(contents[i]) != 0:
                    self.upload_igtv()
                    self.add_count_to_bd("uploaded_igtv")
            if contents[i] == "К":
                if self.count_files(contents[i]) != 0:
                    self.upload_clips()
                    self.add_count_to_bd("uploaded_clips")
            if faza_process[0] == "morning":
                self.set_to_bd("current_position_content", "morning-{}".format(str(i + 1)))
            if faza_process[0] == "day":
                self.set_to_bd("current_position_content", "day-{}".format(str(i + 1)))
            if faza_process[0] == "evening":
                self.set_to_bd("current_position_content", "evening-{}".format(str(i + 1)))
            time.sleep(random.randint(((max_time_sleep*60)-20), max_time_sleep*60))
        self.set_to_bd("{}_process".format(faza_process[0]), 1)
    
    def start(self, morning_time, day_time, evening_time):
        """Запускает цикл автопостинга"""
        if self.loopflag:
            return
        self.loopflag = True
        self.thread = threading.Thread(target=self._run_loop, args=(morning_time, day_time, evening_time))
        self.thread.start()
    
    def _run_loop(self, morning_time, day_time, evening_time):
        """Основной цикл автопостинга (логика из OLD версии)"""
        while self.loopflag:
            current_time = (datetime.now() + timedelta(hours=0)).time()
            if (current_time > datetime.strptime(morning_time[0], "%H:%M:%S").time()):
                if (current_time < datetime.strptime(morning_time[1], "%H:%M:%S").time()):
                    if self.get_from_bd("morning_process"):
                        pass
                    else:
                        self.post("morning_content", datetime.strptime(morning_time[0], "%H:%M:%S").time(),
                                 datetime.strptime(morning_time[1], "%H:%M:%S").time())
                if (current_time > datetime.strptime(day_time[0], "%H:%M:%S").time()):
                    if (current_time < datetime.strptime(day_time[1], "%H:%M:%S").time()):
                        if self.get_from_bd("day_process"):
                            pass
                        else:
                            self.post("day_content", datetime.strptime(day_time[0], "%H:%M:%S").time(),
                                     datetime.strptime(day_time[1], "%H:%M:%S").time())
                    if (current_time > datetime.strptime(evening_time[0], "%H:%M:%S").time()):
                        if (current_time < datetime.strptime(evening_time[1], "%H:%M:%S").time()):
                            if self.get_from_bd("evening_process"):
                                pass
                            else:
                                self.post("evening_content", datetime.strptime(evening_time[0], "%H:%M:%S").time(),
                                         datetime.strptime(evening_time[1], "%H:%M:%S").time())
                        else:
                            self.set_to_bd("morning_process", 0)
                            self.set_to_bd("day_process", 0)
                            self.set_to_bd("evening_process", 0)
            time.sleep(10)
    
    def stop(self):
        """Останавливает цикл автопостинга"""
        self.loopflag = False
        if self.thread:
            self.thread.join()


if __name__ == "__main__":
    print("✅ Модуль scheduler.py загружен успешно!")
