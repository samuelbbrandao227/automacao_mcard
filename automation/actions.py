from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.keys import Keys
from time import sleep
from config import MCARD_LOGIN, MCARD_SENHA, MCARD_URL
from utils.logger import logger

def login(driver):
    """Realiza login no MCard usando credenciais do .env."""
    try:
        logger.info("Acessando o site...")
        driver.get(MCARD_URL)

        wait = WebDriverWait(driver, 15)
        campo_login = wait.until(EC.presence_of_element_located((By.NAME, 'login')))
        campo_login.clear()
        campo_login.send_keys(MCARD_LOGIN + Keys.TAB + MCARD_SENHA + Keys.ENTER)

        # Aguarda tela principal carregar
        wait.until(EC.presence_of_element_located((By.ID, 'manip2'))).click()
        logger.info("Login realizado com sucesso!")
        return True
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        return False

def fazer_recarga(driver, forma_pagamento, numero_cartao, valor, nome_pagador=""):
    """Realiza a recarga no MCard."""
    try:
        logger.info(f"Iniciando recarga - Cartão: {numero_cartao}, Valor: {valor}, Forma: {forma_pagamento}")

        wait = WebDriverWait(driver, 15)

        if forma_pagamento == "PIX":
            Select(driver.find_element("id", "tipoPg")).select_by_value("1")
        
        # Preencher número do cartão
        campo_cartao = wait.until(EC.presence_of_element_located((By.ID, 'nrcartaocredito')))
        campo_cartao.clear()
        campo_cartao.send_keys(numero_cartao)

        # Preencher valor
        campo_acrescido = driver.find_element(By.ID, 'acrescido')
        campo_pagocredito = driver.find_element(By.ID, 'pagocredito')

        campo_acrescido.clear()
        campo_acrescido.send_keys(str(valor))
        campo_pagocredito.clear()
        campo_pagocredito.send_keys(str(valor))

        # Validar
        driver.find_element(By.XPATH, "//button[text()='Validar']").click()

        # Botão de confirmar
        confirm_button = wait.until(EC.presence_of_element_located((By.ID, 'btn-maisCredito')))

        # Captura nome do pagador se não foi informado
        if not nome_pagador:
            try:
                nome_pagador = driver.find_element(By.XPATH, "//div[contains(@class, 'col-md-4')]/span").text
            except:
                nome_pagador = "Desconhecido"

        driver.execute_script("setTimeout(() => arguments[0].click(), 100);", confirm_button)

        logger.info(f"Recarga concluída para {nome_pagador}")
        return True
    except Exception as e:
        logger.error(f"Erro ao realizar recarga: {e}")
        return False

def set_margins(driver, margin_value: str = "1", timeout: int = 10) -> None:
    """
    Abre o diálogo de impressão do Chrome, expande 'Mais configurações',
    define a margem desejada e cancela o diálogo, retornando à janela original.

    Args:
        driver: WebDriver já apontando para a página a ser impressa.
        margin_value: valor da margem no seletor (ex.: "0"=Padrão, "1"=Sem margens, etc. depende do Chrome).
        timeout: tempo máximo (s) para esperas explícitas.
    """
    wait = WebDriverWait(driver, timeout)
    original_handles = set(driver.window_handles)
    original_handle = driver.current_window_handle

    # Abre o preview de impressão
    driver.execute_script("setTimeout(() => window.print(), 100);")

    # Aguarda a nova janela/aba do preview
    wait.until(lambda d: len(d.window_handles) > len(original_handles))
    new_handle = next(iter(set(driver.window_handles) - original_handles))

    try:
        driver.switch_to.window(new_handle)

        # 1) Raiz do preview
        host = wait.until(EC.presence_of_element_located((By.TAG_NAME, "print-preview-app")))
        sr1 = host.shadow_root  # Shadow root do print-preview-app

        # 2) Sidebar
        sidebar = wait.until(lambda d: sr1.find_element(By.CSS_SELECTOR, "print-preview-sidebar"))
        sr2 = sidebar.shadow_root

        # 3) "Mais configurações" (expandir)
        more_settings = wait.until(lambda d: sr2.find_element(By.CSS_SELECTOR, "print-preview-more-settings"))
        sr3 = more_settings.shadow_root
        expand_label = wait.until(lambda d: sr3.find_element(By.CSS_SELECTOR, "cr-expand-button #label"))
        expand_label.click()

        # 4) Margens: localizar o select real dentro do componente e escolher o valor
        margins_sr = wait.until(lambda d: sr2.find_element(By.CSS_SELECTOR, "print-preview-margins-settings")).shadow_root
        # Busca um <select> interno (mais estável do que classe genérica)
        select_el = wait.until(lambda d: margins_sr.find_element(By.CSS_SELECTOR, "select"))
        Select(select_el).select_by_value(margin_value)

        # 5) Botões do rodapé (Cancelar / Imprimir)
        btn_strip_sr = wait.until(lambda d: sr2.find_element(By.CSS_SELECTOR, "print-preview-button-strip")).shadow_root
        cancel_btn = wait.until(lambda d: btn_strip_sr.find_element(By.CSS_SELECTOR, "cr-button.cancel-button"))
        # print_btn = btn_strip_sr.find_element(By.CSS_SELECTOR, "cr-button.action-button")  # se precisar
        cancel_btn.click()

    finally:
        # Sempre volta para a janela original
        driver.switch_to.window(original_handle)

def imprimir_comprovante(driver):
    """Simula clique no botão de imprimir."""
    try:
        wait = WebDriverWait(driver, 15)
        all_windows = driver.window_handles
        while len(all_windows) <= 1:
            all_windows = driver.window_handles
            sleep(0.3)
        driver.switch_to.window(all_windows[1])

        wait.until(EC.presence_of_element_located((By.TAG_NAME, "print-preview-app")))
        host_element = driver.find_element(By.TAG_NAME, "print-preview-app")
        shadow_root_1 = driver.execute_script("return arguments[0].shadowRoot", host_element)
        inner_host_1 = shadow_root_1.find_element(By.CSS_SELECTOR, "print-preview-sidebar")
        shadow_root_2 = driver.execute_script("return arguments[0].shadowRoot", inner_host_1)
        inner_host_2 = shadow_root_2.find_element(By.CSS_SELECTOR, "print-preview-button-strip")
        shadow_root_3 = driver.execute_script("return arguments[0].shadowRoot", inner_host_2)
        button = shadow_root_3.find_element(By.CLASS_NAME, "action-button")
        button.click()

        driver.switch_to.window(all_windows[0])
        logger.info("Comprovante enviado para impressão.")
        return True
    except Exception as e:
        logger.error(f"Erro ao imprimir comprovante: {e}")
        return False
