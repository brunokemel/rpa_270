import os
import random
import time
import subprocess
from pathlib import Path
import requests
import speech_recognition as sr
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

class RecaptchaSolver:
    def __init__(self, driver):
        self.driver = driver

    def download_audio(self, url, path):
        response = requests.get(url)
        with open(path, 'wb') as f:
            f.write(response.content)
        print("Audio baixado com sucesso.")

    def solveCaptcha(self):
        try:
            time.sleep(2)
            self.driver.switch_to.default_content()
            
            try:
                iframe_challenge = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'api2/bframe')]"))
                )
                self.driver.switch_to.frame(iframe_challenge)
                
                image_captcha = self.driver.find_element(By.ID, 'rc-imageselect')
                if image_captcha:
                    print("Captcha de imagem detectado. Mudando para áudio...")
                    
                    audio_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.ID, 'recaptcha-audio-button'))
                    )
                    audio_button.click()
                    print("Clicou no botão de áudio.")
                    
                    time.sleep(2)
                    self.solveAudioCaptchaDirectly()
                    
            except Exception as e:
                print(f"Captcha de imagem não encontrado ou erro: {e}")
                self.driver.switch_to.default_content()

        except Exception as e:
            print(f"An error occurred while solving CAPTCHA: {e}")
            self.driver.switch_to.default_content()
            raise

    def solveAudioCaptchaDirectly(self):
        try:
            audio_source = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'audio-source'))
            ).get_attribute('src')
            print(f"Audio source URL: {audio_source}")
            
            # Caminho do ffmpeg
            #ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe" if os.path.exists(r"C:\ffmpeg\bin\ffmpeg.exe") else "ffmpeg"
            ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"

            # Diretório temporário (igual ao primeiro código)
            temp_dir = os.getenv("TEMP") if os.name == "nt" else "/tmp/"
            temp_dir = Path(temp_dir)

            # Caminhos dos arquivos (mantendo a lógica da primeira)
            path_to_mp3 = temp_dir / f"{random.randrange(1, 1000)}.mp3"
            path_to_wav = temp_dir / f"{random.randrange(1, 1000)}.wav"

            # Aqui você baixa o áudio
            self.download_audio(audio_source, path_to_mp3)

            # Converter MP3 para WAV usando ffmpeg
            if not path_to_mp3.exists():
                raise FileNotFoundError(f"MP3 não encontrado: {path_to_mp3}")
            
            path_to_mp3 = str(path_to_mp3.resolve())
            path_to_wav = str(path_to_wav.resolve())

            subprocess.run(f'"{ffmpeg_path}" -y -i "{path_to_mp3}" "{path_to_wav}"', shell=True, check=True)
            print("Converted MP3 to WAV.")

            # Reconhecer áudio
            recognizer = sr.Recognizer()
            with sr.AudioFile(path_to_wav) as source:
                audio = recognizer.record(source)

            captcha_text = recognizer.recognize_google(audio).lower()
            print(f"Recognized CAPTCHA text: {captcha_text}")

            audio_response = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, 'audio-response'))
            )
            audio_response.send_keys(captcha_text)
            audio_response.send_keys(Keys.ENTER)
            print("Entered and submitted CAPTCHA text.")

            time.sleep(2)
            self.driver.switch_to.default_content()
            
            if self.isSolved():
                print("Audio CAPTCHA solved.")
            else:
                print("Failed to solve audio CAPTCHA.")
                raise Exception("Failed to solve CAPTCHA")

        except Exception as e:
            print(f"An error occurred while solving audio CAPTCHA: {e}")
            self.driver.switch_to.default_content()
            raise

        finally:
            self.driver.switch_to.default_content()

    def isSolved(self):
        try:
            self.driver.switch_to.default_content()

            try:
                iframe_check = self.driver.find_element(By.XPATH, "//iframe[contains(@src, 'api2/bframe')]")
                print("Captcha ainda presente na página.")
                return False
            except:
                print("Captcha não encontrado - provavelmente resolvido.")
                return True

        except Exception as e:
            print(f"An error occurred while checking if CAPTCHA is solved: {e}")
            return False