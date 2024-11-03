import base64
from time import sleep
from typing import Dict

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from python.exceptions.CorrectAnswerNotFoundError import CorrectAnswerNotFoundError

CHROME_DRIVER_ROUTE = r'C:\Users\G513\Downloads\chromedriver-win64\chromedriver.exe'
CORRECT_ANSWER_IMAGE_BYTES = open("./resources/check.png", "rb").read()
PAGE_TO_SCRAP_URL = 'https://www.daypo.com/ic-01.html#test'
QUESTIONS_AND_CORRECT_ANSWERS_DICT: Dict[str, str] = {}


def start_test_scraping():
    driver = configure_selenium_driver()
    driver.get(PAGE_TO_SCRAP_URL)
    print("Página cargada correctamente.")

    accept_cookies(driver)
    navigate_through_questions(driver)
    write_questions_with_correct_answer_on_txt()

    driver.quit()


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


def navigate_through_questions(driver):
    questions_number = obtain_questions_number(driver)

    for x in range(questions_number):
        answers_table = driver.find_element(By.ID, "cuestiones1").find_element(By.CLASS_NAME, "w")
        first_answer_button = answers_table.find_element(By.ID, "op0")
        next_button = driver.find_element(By.ID, "boton")
        question = driver.find_element(By.ID, "pri1").text

        first_answer_button.click()
        next_button.click()

        answers_table = driver.find_element(By.ID, "cuestiones1").find_element(By.CLASS_NAME, "w")

        correct_answer = search_correct_answer(driver, answers_table, question)
        QUESTIONS_AND_CORRECT_ANSWERS_DICT[question] = correct_answer
        next_button.click()


# Obtiene el numero de preguntas, Ej de 1/23 obtendra el 23 y lo transformara a int
def obtain_questions_number(driver) -> int:
    questions_number: str = driver.find_element(By.ID, "cuestion").text.split("/")[1]
    return int(questions_number)


# Busca la respuesta correcta de la pregunta comparando las imagenes, buscando la que sea el check
def search_correct_answer(driver: WebDriver, answer_table: WebElement, question: str) -> str:
    answers = answer_table.find_elements(By.TAG_NAME, "tr")
    image_number = 0  # Quizas remplazar por una letra? todo

    for answer in answers:
        scraped_image_path = obtain_and_decode_image_from_answer(driver, answer, str(image_number))

        if CORRECT_ANSWER_IMAGE_BYTES == open(scraped_image_path, "rb").read():
            return answer.find_element(By.CLASS_NAME, "pr05").text

        image_number += 1

    raise CorrectAnswerNotFoundError(f"No se ha podido encontrar la respuesta correcta a la pregunta: {question}")


# Obtiene la imagen de la pagina en base64, la decodifica para crear el png y regresar su ruta
def obtain_and_decode_image_from_answer(driver: WebDriver, questions_table: WebElement, name: str) -> str:
    image = questions_table.find_element(By.CSS_SELECTOR, "canvas[id^='vai']")
    data_url = driver.execute_script("return arguments[0].toDataURL('image/png');", image)

    image_data = data_url.split(",")[1]
    image_path = f"./temp/answer_img_{name}.png"
    with open(image_path, "wb") as file:
        file.write(base64.b64decode(image_data))

    return image_path


# Escribe las preguntas con sus respuestas correctas en un txt
def write_questions_with_correct_answer_on_txt() -> None:
    file_name = create_file_name()

    with open(file_name, "w") as file:
        for question, answer in QUESTIONS_AND_CORRECT_ANSWERS_DICT.items():
            file.write(f"{question} ----> {answer}\n\n")
            file.write("----------------------------------------------------------\n\n")


# Utiliza la url de la pagina para crear el nombre del txt dodne se guardaran las respuestas
def create_file_name() -> str:
    page_name = PAGE_TO_SCRAP_URL.rsplit("/", 1)[-1]
    base_name = page_name.replace("#", "").replace(".", "")
    file_name = base_name + ".txt"
    return file_name


if __name__ == "__main__":
    start_test_scraping()
