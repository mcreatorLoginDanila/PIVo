# image_viewer.pyw

import sys
import os
from tkinter import filedialog
import ctypes # для получения информации о разрешении экрана

# --- Сторонние библиотеки ---
import customtkinter as ctk
from PIL import Image, UnidentifiedImageError

# --- Только для Windows ---
try:
    import winreg
    IS_WINDOWS = True
except ImportError:
    IS_WINDOWS = False

# --- Константы ---
APP_NAME = "Python Image Viewer"
PROG_ID = "PythonImageViewer.App" # Уникальный ID для регистрации в реестре
SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.webp']

# --- Класс для работы с реестром Windows ---
class RegistryHandler:
    """ Управляет регистрацией и разрегистрацией файловых ассоциаций в Windows. """
    
    def get_exe_path(self):
        """ Получает путь к исполняемому файлу (.exe или .pyw) """
        if getattr(sys, 'frozen', False):  # Если приложение скомпилировано в .exe
            return sys.executable
        return os.path.abspath(sys.argv[0]) # Путь к скрипту .pyw

    def register(self):
        """ Регистрирует приложение для открытия поддерживаемых форматов. """
        if not IS_WINDOWS:
            self.show_message("Ошибка", "Регистрация форматов поддерживается только в Windows.")
            return

        exe_path = self.get_exe_path()
        try:
            # Создаем ключ для нашего приложения
            key_path = fr"Software\Classes\{PROG_ID}"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValue(key, None, winreg.REG_SZ, APP_NAME)
                
                # Команда для открытия файла
                with winreg.CreateKey(key, r"shell\open\command") as command_key:
                    command = f'"{exe_path}" "%1"'
                    winreg.SetValue(command_key, None, winreg.REG_SZ, command)
                
                # Иконка по умолчанию (из самого exe)
                with winreg.CreateKey(key, r"DefaultIcon") as icon_key:
                    winreg.SetValue(icon_key, None, winreg.REG_SZ, f'"{exe_path}",0')

            # Ассоциируем расширения с нашим приложением
            for ext in SUPPORTED_EXTENSIONS:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, fr"Software\Classes\{ext}") as ext_key:
                    winreg.SetValue(ext_key, None, winreg.REG_SZ, PROG_ID)
            
            self.show_message("Успех", "Приложение успешно зарегистрировано!")

        except Exception as e:
            self.show_message("Ошибка регистрации", f"Не удалось зарегистрировать приложение:\n{e}")

    def unregister(self):
        """ Удаляет регистрацию приложения. """
        if not IS_WINDOWS:
            self.show_message("Ошибка", "Эта функция доступна только в Windows.")
            return
            
        try:
            # Просто удаляем ключ нашего приложения. Windows сама разберется с остальным.
            # Это безопаснее, чем пытаться восстановить предыдущие значения.
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, fr"Software\Classes\{PROG_ID}\shell\open\command")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, fr"Software\Classes\{PROG_ID}\shell\open")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, fr"Software\Classes\{PROG_ID}\shell")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, fr"Software\Classes\{PROG_ID}\DefaultIcon")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, fr"Software\Classes\{PROG_ID}")

            self.show_message("Успех", "Регистрация приложения удалена.")
        except FileNotFoundError:
            self.show_message("Информация", "Приложение не было зарегистрировано.")
        except Exception as e:
            self.show_message("Ошибка", f"Не удалось удалить регистрацию:\n{e}")

    def show_message(self, title, message):
        """ Показывает простое окно с сообщением """
        msg_box = ctk.CTkToplevel()
        msg_box.title(title)
        msg_box.geometry("400x150")
        msg_box.attributes("-topmost", True)
        label = ctk.CTkLabel(msg_box, text=message, wraplength=380)
        label.pack(expand=True, padx=20, pady=20)
        close_button = ctk.CTkButton(msg_box, text="OK", command=msg_box.destroy)
        close_button.pack(pady=10)
        msg_box.transient() # Окно поверх главного
        msg_box.grab_set() # Модальное

# --- Окно настроек ---
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Настройки")
        self.geometry("400x200")
        self.transient(master)
        self.grab_set()

        self.registry_handler = RegistryHandler()
        
        self.label = ctk.CTkLabel(self, text="Зарегистрировать это приложение\nдля открытия файлов изображений:", justify="center")
        self.label.pack(pady=20, padx=20)
        
        self.register_button = ctk.CTkButton(self, text="Зарегистрировать", command=self.registry_handler.register)
        self.register_button.pack(pady=10)
        
        self.unregister_button = ctk.CTkButton(self, text="Удалить регистрацию", fg_color="red", hover_color="darkred", command=self.registry_handler.unregister)
        self.unregister_button.pack(pady=10)

# --- Основное приложение ---
class ImageViewerApp(ctk.CTk):
    def __init__(self, file_path=None):
        super().__init__()

        # --- Настройка окна ---
        self.title(APP_NAME)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width//2}x{screen_height//2}") # Стартовый размер - половина экрана
        ctk.set_appearance_mode("Dark")

        # --- Виджеты ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.image_label = ctk.CTkLabel(self, text="Откройте файл (Ctrl+O) или перетащите его сюда", text_color="gray")
        self.image_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # --- Фрейм для кнопок ---
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.grid(row=1, column=0, pady=10)
        
        self.open_button = ctk.CTkButton(self.button_frame, text="Открыть...", command=self.open_file_dialog)
        self.open_button.pack(side="left", padx=10)

        self.settings_button = ctk.CTkButton(self.button_frame, text="Настройки", command=self.open_settings)
        self.settings_button.pack(side="left", padx=10)

        # --- Горячие клавиши ---
        self.bind("<Control-o>", lambda event: self.open_file_dialog())
        
        # --- Загрузка изображения при запуске ---
        if file_path:
            self.load_image(file_path)

    def open_file_dialog(self):
        """ Открывает диалог выбора файла и загружает изображение """
        file_types = [("Image Files", ' '.join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)), ("All files", "*.*")]
        path = filedialog.askopenfilename(title="Выберите изображение", filetypes=file_types)
        if path:
            self.load_image(path)

    def load_image(self, path):
        """ Загружает и отображает изображение, подгоняя его под размер окна """
        try:
            pil_image = Image.open(path)
            self.display_image(pil_image)
            self.title(f"{os.path.basename(path)} - {APP_NAME}")
        except FileNotFoundError:
            self.image_label.configure(text=f"Файл не найден:\n{path}", image=None)
        except UnidentifiedImageError:
             self.image_label.configure(text=f"Не удалось распознать формат файла:\n{path}", image=None)
        except Exception as e:
            self.image_label.configure(text=f"Произошла ошибка:\n{e}", image=None)
            
    def display_image(self, pil_image):
        """ Масштабирует и отображает изображение """
        # Получаем размеры виджета и изображения
        label_width = self.image_label.winfo_width()
        label_height = self.image_label.winfo_height()
        img_width, img_height = pil_image.size

        # Чтобы избежать деления на ноль при первом запуске
        if label_width < 2 or label_height < 2:
            self.after(100, lambda: self.display_image(pil_image))
            return

        # Рассчитываем соотношения сторон и масштабируем
        ratio = min(label_width / img_width, label_height / img_height)
        new_size = (int(img_width * ratio), int(img_height * ratio))
        
        # Используем LANCZOS для качественного ресайза
        resized_image = pil_image.resize(new_size, Image.LANCZOS)

        # Создаем CTkImage и обновляем виджет
        ctk_image = ctk.CTkImage(light_image=resized_image, dark_image=resized_image, size=new_size)
        self.image_label.configure(text="", image=ctk_image)
        self.image_label.image = ctk_image # Сохраняем ссылку

    def open_settings(self):
        SettingsWindow(self)


if __name__ == "__main__":
    # Проверяем, был ли передан файл как аргумент командной строки
    # (например, при двойном клике на ассоциированный файл)
    file_to_open = None
    if len(sys.argv) > 1:
        file_to_open = sys.argv[1]

    app = ImageViewerApp(file_path=file_to_open)
    app.mainloop()