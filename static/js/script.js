document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("recargaForm");
    const formaSelect = document.getElementById("forma_pagamento");
    const nomePagador = document.getElementById("nome_pagador");
    const numeroCartao = document.getElementById("numero_cartao");
    const valorField = document.getElementById("valor");
  
    const groups = {
      forma: document.getElementById("group-forma"),
      nome: document.getElementById("group-nome"),
      cartao: document.getElementById("group-cartao"),
      valor: document.getElementById("group-valor"),
      submit: document.getElementById("group-submit")
    };
  
    const containers = {
      form: document.getElementById("formContent"),
      loading: document.getElementById("loadingContainer"),
      success: document.getElementById("successContainer"),
      error: document.getElementById("errorContainer")
    };
  
    const main = document.getElementById("mainContainer");
    const panel = document.getElementById("panel");
    let pollInterval = null;
  
    function show(el) {
      el.classList.remove("is-hidden");
      el.classList.add("is-enter");
    }
    
    function hide(el, callback) {
      if (!el) return;
      const hadEnter = el.classList.contains("is-enter");
  
      el.classList.remove("is-enter");
      el.classList.add("is-hidden");
  
      if (typeof callback === "function") {
          if (!hadEnter) {
          // Se já estava escondido, chama direto
          callback();
          } else {
          const handler = (ev) => {
              if (ev.propertyName === "max-height") {
              el.removeEventListener("transitionend", handler);
              callback();
              }
          };
          el.addEventListener("transitionend", handler);
          }
      }
    }
  
    // ===== Função para validar e mostrar campos baseado nos valores atuais =====
    function updateFieldsVisibility() {
      const forma = formaSelect.value;
      const nomeValue = nomePagador.value.trim();
      const cartaoValue = numeroCartao.value.trim();
      const valorValue = valorField.value.trim();
  
      if (forma === "PIX") {
        // PIX: forma → nome → cartão → valor → submit
        show(groups.nome);
        
        if (nomeValue.length > 0) {
          show(groups.cartao);
          
          if (/^\d{4,6}$/.test(cartaoValue)) {
            show(groups.valor);
            
            const num = parseFloat(valorValue.replace(",", "."));
            if (valorValue.length > 0 && num > 0) {
              show(groups.submit);
            } else {
              hide(groups.submit);
            }
          } else {
            hide(groups.valor);
            hide(groups.submit);
          }
        } else {
          hide(groups.cartao);
          hide(groups.valor);
          hide(groups.submit);
        }
        
      } else if (forma === "DINHEIRO") {
        // DINHEIRO: forma → cartão → valor → submit
        hide(groups.nome);
        show(groups.cartao);
        
        if (/^\d{4,6}$/.test(cartaoValue)) {
          show(groups.valor);
          
          const num = parseFloat(valorValue.replace(",", "."));
          if (valorValue.length > 0 && num > 0) {
            show(groups.submit);
          } else {
            hide(groups.submit);
          }
        } else {
          hide(groups.valor);
          hide(groups.submit);
        }
      } else {
        // Nenhuma forma selecionada - esconde todos exceto forma
        hide(groups.nome);
        hide(groups.cartao);
        hide(groups.valor);
        hide(groups.submit);
      }
    }
  
    // ===== Event Listeners =====
    formaSelect.addEventListener("change", () => {
      updateFieldsVisibility();
    });
  
    nomePagador.addEventListener("input", () => {
      if (formaSelect.value === "PIX") {
        updateFieldsVisibility();
      }
    });
  
    numeroCartao.addEventListener("input", () => {
      updateFieldsVisibility();
    });
  
    valorField.addEventListener("input", () => {
      updateFieldsVisibility();
    });
  
    // ===== Submit + Polling =====
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
  
      const payload = {
        forma_pagamento: formaSelect.value,
        nome_pagador: nomePagador.value,
        numero_cartao: numeroCartao.value,
        valor: valorField.value
      };
  
      const csrfToken = form.querySelector("input[name='csrf_token']").value;
      try {
        const res = await fetch("/recarregar", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
          },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
          startLoading(data.task_id);
        } else {
          showError(data.message || "Erro ao iniciar recarga.");
        }
      } catch {
        showError("Falha na conexão com o servidor.");
      }
    });
  
    function startLoading(taskId) {
      main.setAttribute("aria-busy", "true");
  
      // Esconde todos os grupos de campos
      containers.form.querySelectorAll(".form-group").forEach(group => hide(group));
      hide(containers.success);
      hide(containers.error);
  
      // Quando form terminar de colapsar → mostra loading
      hide(containers.form, () => {
        show(containers.loading);
      });
  
      pollInterval = setInterval(async () => {
        try {
          const res = await fetch(`/status/${taskId}`);
          const status = await res.json();
          if (status.status === "completed") {
            clearInterval(pollInterval);
            showSuccess();
          } else if (status.status === "failed") {
            clearInterval(pollInterval);
            showError(status.message || "Falha na recarga.");
          }
        } catch {
          clearInterval(pollInterval);
          showError("Erro ao verificar status da recarga.");
        }
      }, 1000);
    }
  
    function showSuccess() {
      hide(containers.loading, () => show(containers.success));
      setTimeout(resetForm, 2500);
    }
  
    function showError(msg) {
      hide(containers.loading);
      hide(containers.success);
      document.getElementById("errorMessage").textContent = msg || "Erro desconhecido.";
      show(containers.error);
      panel.classList.add("is-error");
      setTimeout(() => panel.classList.remove("is-error"), 600);
      setTimeout(resetForm, 3000);
    }
  
    function resetForm() {
      main.setAttribute("aria-busy", "false");
      form.reset();
  
      show(containers.form);
      hide(containers.loading);
      hide(containers.success);
      hide(containers.error);
  
      show(groups.forma);
      hide(groups.nome);
      hide(groups.cartao);
      hide(groups.valor);
      hide(groups.submit);
    }
  
    // ===== Inicialização =====
    // Verifica campos preenchidos na inicialização (útil para refresh da página)
    updateFieldsVisibility();
  });