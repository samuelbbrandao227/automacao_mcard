# app.py

from flask import Flask, render_template, request, jsonify
from automation.driver import iniciar_driver
from automation.actions import login, fazer_recarga, imprimir_comprovante, set_margins
from forms import RecargaForm
from utils.logger import logger
from automation.google_sheets import adicionar_recarga_txt
import webbrowser
import threading
import os
import uuid # Para gerar IDs de tarefa únicos

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'uma-chave-secreta-de-fallback')

# --- NOVO: Task Store ---
# Um dicionário em memória para rastrear o estado das tarefas de recarga.
# Em um app real/maior, usaríamos Redis ou um banco de dados.
tasks = {}

# --- FUNÇÃO WORKER (EXECUTADA EM SEGUNDO PLANO) ---
def run_recharge_task(task_id: str, driver_instance, form_data: dict):
    """
    Esta função executa a automação demorada do Selenium.
    Ela atualiza o dicionário 'tasks' com o resultado.
    """
    logger.info(f"Iniciando tarefa de recarga em background: {task_id}")
    try:
        # Extrai os dados do dicionário
        forma_pagamento = form_data.get('forma_pagamento')
        nome_pagador = form_data.get('nome_pagador')
        numero_cartao = form_data.get('numero_cartao')
        valor = form_data.get('valor')

        sucesso_recarga = fazer_recarga(driver_instance, forma_pagamento, numero_cartao, valor, nome_pagador)

        if sucesso_recarga:
            # Tenta imprimir e adicionar ao Google Sheets, mas não falha a tarefa inteira se isso der erro.
            try:
                imprimir_comprovante(driver_instance)
            except Exception as e:
                logger.error(f"TASK {task_id}: Erro ao imprimir comprovante: {e}")
            
            try:
                if forma_pagamento == "PIX":
                    adicionar_recarga_txt(nome_pagador, valor, numero_cartao)
            except Exception as e:
                logger.error(f"TASK {task_id}: Erro ao adicionar no Google Sheets: {e}")
            
            # Atualiza o status da tarefa para sucesso
            tasks[task_id] = {'status': 'completed', 'message': f"Recarga de R${valor} para o cartão {numero_cartao} concluída com sucesso!"}
        else:
            # Atualiza o status da tarefa para falha
            tasks[task_id] = {'status': 'failed', 'message': "Falha ao processar recarga. O site pode ter retornado um erro."}
            
    except Exception as e:
        logger.error(f"TASK {task_id}: Erro inesperado na automação: {e}")
        tasks[task_id] = {'status': 'failed', 'message': f"Erro crítico durante a automação: {e}"}
    logger.info(f"TASK {task_id}: Função da thread finalizada. Status final: {tasks.get(task_id, {}).get('status')}")


# --- ROTA PRINCIPAL (APENAS RENDERIZA A PÁGINA) ---
@app.route("/", methods=["GET"])
def index():
    form = RecargaForm()
    return render_template("index.html", form=form)


# --- NOVO ENDPOINT: INICIAR RECARGA ---
@app.route("/recarregar", methods=["POST"])
def recarregar():
    """
    Recebe os dados, cria uma tarefa, inicia a execução em background
    e retorna imediatamente um ID de tarefa.
    """
    data = request.get_json()
    
    # Validação básica
    if not all(k in data for k in ['forma_pagamento', 'numero_cartao', 'valor']):
        return jsonify({"success": False, "message": "Dados do formulário inválidos."}), 400

    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'pending', 'message': 'Recarga em processamento...'}
    
    # Inicia a automação em uma thread separada para não bloquear a resposta
    # NOTA: Passamos a instância global 'driver' para a thread.
    # Em ambientes multi-usuário, isso seria um problema de concorrência.
    # Para uma aplicação desktop local, é uma simplificação aceitável.
    thread = threading.Thread(target=run_recharge_task, args=(task_id, driver, data))
    thread.start()
    
    logger.info(f"Tarefa {task_id} criada para o cartão {data.get('numero_cartao')}.")
    
    # Retorna o ID da tarefa para o frontend poder consultar o status
    return jsonify({"success": True, "task_id": task_id}), 202


# --- NOVO ENDPOINT: VERIFICAR STATUS DA TAREFA ---
@app.route("/status/<task_id>", methods=["GET"])
def status(task_id):
    """
    Endpoint para o frontend fazer polling e verificar o estado da tarefa.
    """
    task = tasks.get(task_id)
    
    logger.info(f"STATUS CHECK para TASK {task_id}: Status encontrado: {task.get('status') if task else 'Nenhum'}")
    if not task:
        return jsonify({'status': 'failed', 'message': 'Tarefa não encontrada.'}), 404
        
    return jsonify(task)


# Função para abrir o navegador (sem mudanças)
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    driver = iniciar_driver()
    set_margins(driver)

    if not login(driver):
        logger.error("NÃO FOI POSSÍVEL FAZER LOGIN. O APLICATIVO NÃO FUNCIONARÁ.")
        # Poderíamos até fechar o app aqui, mas vamos deixar rodando para debug.
    
    threading.Timer(1.5, open_browser).start()
    
    # Use 'threaded=True' para o servidor de desenvolvimento do Flask lidar melhor
    # com a thread de background, embora a arquitetura de polling já resolva o bloqueio.
    app.run(threaded=True)