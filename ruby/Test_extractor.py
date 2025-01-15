import base64
import configparser
import string
import time
from pathlib import Path
from typing import Dict

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from python.exceptions.CorrectAnswerNotFoundError import CorrectAnswerNotFoundError

config = configparser.ConfigParser()
config.read("./config/personal.ini")

CHROME_DRIVER_ROUTE = config["Paths"]["CHROME_DRIVER_ROUTE"]
FILE_WITH_ANSWERS_PATH = Path(config["Paths"]["FILE_WITH_ANSWERS_PATH"])
PAGE_TO_SCRAP_URL = config["URLs"]["PAGE_TO_SCRAP_URL"]

CORRECT_ANSWER_IMAGE_BYTES = open("./resources/check.png", "rb").read()
QUESTIONS_AND_CORRECT_ANSWERS_DICT: Dict[str, list[str]] = {}
TEMPORAL_FILE_PATH = Path('./temp/')


# Inicia el programa y al finalizar elimina los archivos temporales
def start_test_scraping():
    try:
        TEMPORAL_FILE_PATH.mkdir(exist_ok=True)

        driver = configure_selenium_driver()
        driver.get(PAGE_TO_SCRAP_URL)
        print("Página cargada correctamente.")

        accept_cookies(driver)
        find_correct_answers_from_questions(driver)
        write_questions_with_correct_answer_on_txt()

        driver.quit()

    finally:
        delete_temporal_files()


# Acepta las cookies si es necesario
def accept_cookies(driver) -> None:
    time.sleep(1)
    cookies = driver.find_elements(By.ID, "ez-accept-all")
    if cookies:
        cookies[0].click()
        print("Cookies aceptadas.")
    else:
        print("No hay cookies.")


# Configura el driver de selenium
def configure_selenium_driver() -> webdriver:
    chrome_options: chr = Options()
    chrome_options.add_argument("--no-sandbox")
    service = Service(CHROME_DRIVER_ROUTE)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


# Lee todas las preguntas y analiza cuales son las respuestas correctas
def find_correct_answers_from_questions(driver) -> None:
    questions_number = obtain_questions_number(driver)
    next_button = driver.find_element(By.ID, "boton")

    for x in range(questions_number):
        answers_table = driver.find_element(By.ID, "cuestiones1").find_element(By.CLASS_NAME, "w")
        question = driver.find_element(By.ID, "pri1").text

        click_first_answer(answers_table)
        next_button.click()

        answers_table = driver.find_element(By.ID, "cuestiones1").find_element(By.CLASS_NAME, "w")

        correct_answer = search_correct_answer(driver, answers_table, question)
        QUESTIONS_AND_CORRECT_ANSWERS_DICT[question] = correct_answer
        next_button.click()


# Presiona la primera respuesta
def click_first_answer(answers_table) -> None:
    try:
        first_answer_button = answers_table.find_element(By.ID, "op0")
        first_answer_button.click()
    except NoSuchElementException:
        first_answer_button = answers_table.find_element(By.ID, "ch0")
        first_answer_button.click()


# Obtiene el numero de preguntas, Ej de 1/23 obtendra el 23 y lo transformara a int
def obtain_questions_number(driver) -> int:
    questions_number: str = driver.find_element(By.ID, "cuestion").text.split("/")[1]
    return int(questions_number)


# Busca las respuestas correcta de la pregunta comparando las imagenes, buscando las que sean el check
def search_correct_answer(driver: WebDriver, answer_table: WebElement, question: str) -> list[str]:
    answers = answer_table.find_elements(By.TAG_NAME, "tr")
    correct_answers_list: list[str] = []

    for image_number, answer in zip(string.ascii_lowercase, answers):
        scraped_image_path = obtain_and_decode_image_from_answer(driver, answer, image_number)

        if CORRECT_ANSWER_IMAGE_BYTES == open(scraped_image_path, "rb").read():
            correct_answer = answer.find_element(By.CLASS_NAME, "pr05").text
            correct_answers_list.append(correct_answer)

    if correct_answers_list:
        return correct_answers_list

    raise CorrectAnswerNotFoundError(f"No se ha podido encontrar la respuesta correcta a la pregunta: {question}")


# Obtiene la imagen de la pagina en base64, la decodifica para crear el png y regresar su ruta
def obtain_and_decode_image_from_answer(driver: WebDriver, questions_table: WebElement, name: str) -> str:
    image = questions_table.find_element(By.CSS_SELECTOR, "canvas[id^='vai']")
    data_url = driver.execute_script("return arguments[0].toDataURL('image/png');", image)

    image_data = data_url.split(",")[1]
    image_path = TEMPORAL_FILE_PATH / f"answer_img_{name}.png"
    with open(image_path, "wb") as file:
        file.write(base64.b64decode(image_data))

    return str(image_path)


# Escribe las preguntas con sus respuestas correctas en un txt
def write_questions_with_correct_answer_on_txt() -> None:
    file_name = create_file_name()

    with open(file_name, "w") as file:
        for question, answers in QUESTIONS_AND_CORRECT_ANSWERS_DICT.items():
            answers_text = "\n".join(answers)
            file.write(f"{question} ----> \n{answers_text}\n\n")
            file.write("----------------------------------------------------------\n\n")

# Utiliza la url de la pagina para crear el nombre del txt dodne se guardaran las respuestas, que se concatenara al
# path puesto
def create_file_name() -> str:
    page_name = PAGE_TO_SCRAP_URL.rsplit("/", 1)[-1]
    base_name = page_name.replace("#", "").replace(".", "")
    file_name = base_name + ".txt"

    return str(FILE_WITH_ANSWERS_PATH / file_name)


# Elimina los archivos temporales
def delete_temporal_files() -> None:
    folder = Path(TEMPORAL_FILE_PATH)
    for item in folder.iterdir():
        if item.is_file() or item.is_symlink():
            item.unlink()


if __name__ == "__main__":
    start_test_scraping()
