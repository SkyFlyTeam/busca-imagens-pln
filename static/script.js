const form = document.getElementById("form");
const input = document.getElementById("pergunta");
const botao = form.querySelector("button");
const mensagem = document.getElementById("mensagem");
const confianca = document.getElementById("confianca");
const resultados = document.getElementById("resultados");
const debugConteudo = document.getElementById("debug-conteudo");
const painelDebug = document.getElementById("painel-debug");

const ROTULO_CATEGORIA = {
  vegetacao: "Vegetação",
  solo_exposto: "Solo exposto",
  agua: "Água",
};

function limparResultados() {
  resultados.innerHTML = "";
}

function criar(tag, classe, texto) {
  const el = document.createElement(tag);
  if (classe) el.className = classe;
  if (texto !== undefined) el.textContent = texto;
  return el;
}

function mostrarConfianca(dados) {
  confianca.classList.remove("escondido", "baixa", "media");

  if (dados.intencao === null) {
    confianca.textContent = "intenção não reconhecida";
    confianca.classList.add("baixa");
    return;
  }

  const pct = Math.round(dados.score * 100);
  confianca.textContent = `confiança: ${pct}%`;

  if (dados.score < 0.4) {
    confianca.classList.add("media");
  }
}

function renderizarCards(itens) {
  limparResultados();

  for (const item of itens) {
    const card = criar("article", "card");

    const img = document.createElement("img");
    img.src = item.url;
    img.alt = `Imagem de ${item.categoria}`;
    img.loading = "lazy";

    const info = criar("div", "card-info");
    const titulo = criar("div", "card-titulo");
    titulo.append(
      criar("strong", "", ROTULO_CATEGORIA[item.categoria_id] || item.categoria),
      criar("span", `selo ${item.origem_id}`, item.origem)
    );

    const meta = criar("p", "card-meta");
    meta.append(
      criar("span", "", item.data),
      criar("span", "", `#${String(item.id).padStart(2, "0")}`)
    );

    info.append(titulo, meta);
    card.append(img, info);
    resultados.appendChild(card);
  }
}

function linhaDebug(rotulo, valor) {
  const linha = criar("div", "debug-linha");
  linha.append(criar("span", "rotulo", rotulo));

  if (Array.isArray(valor)) {
    linha.appendChild(criar("code", "", valor.length ? valor.join(" · ") : "(vazio)"));
  } else {
    linha.appendChild(criar("code", "", valor || "(vazio)"));
  }
  return linha;
}

function renderizarDebug(dados) {
  const debug = dados.debug;
  debugConteudo.innerHTML = "";

  if (!debug) {
    debugConteudo.appendChild(criar("p", "dica", "Sem informações de debug."));
    return;
  }

  const grade = criar("div", "debug-grid");

  // Coluna 1: etapas do pipeline
  const etapas = criar("div", "debug-bloco");
  etapas.appendChild(criar("h3", "", "Pipeline de PLN"));
  etapas.appendChild(linhaDebug("1. normalizado", debug.normalizado));
  etapas.appendChild(linhaDebug("2. corrigido", debug.corrigido));
  etapas.appendChild(linhaDebug("3. canônico", debug.canonico));
  etapas.appendChild(linhaDebug("4. tokens", debug.tokens));
  etapas.appendChild(linhaDebug("5. stems (BOW)", debug.stems));
  etapas.appendChild(linhaDebug("6. texto do BOW", debug.bow));
  etapas.appendChild(linhaDebug("limiar", String(debug.limiar)));
  grade.appendChild(etapas);

  // Coluna 2: ranking de intenções
  const ranking = criar("div", "debug-bloco");
  ranking.appendChild(criar("h3", "", "Top 3 intenções (cosseno)"));

  const top = debug.top || [];
  const maior = top.length ? Math.max(...top.map((t) => t.score), 0.0001) : 1;

  top.forEach((item, indice) => {
    const bloco = criar("div", "top-item");
    const cabecalho = criar("div", "top-cabecalho");
    cabecalho.append(
      criar("strong", "", `${indice + 1}. ${item.descricao || item.intencao}`),
      criar("span", "", item.score.toFixed(3))
    );

    const barra = criar("div", `barra ${indice === 0 ? "vencedora" : ""}`);
    const preenchimento = document.createElement("span");
    preenchimento.style.width = `${Math.min(100, (item.score / maior) * 100)}%`;
    barra.appendChild(preenchimento);

    bloco.append(cabecalho, barra);
    ranking.appendChild(bloco);
  });

  if (debug.sql) {
    ranking.appendChild(criar("h3", "", "SQL executada"));
    ranking.appendChild(criar("pre", "sql-box", debug.sql));
    ranking.appendChild(
      linhaDebug("parâmetros", JSON.stringify(debug.params))
    );
  } else {
    ranking.appendChild(
      criar("p", "dica", "Nenhuma SQL foi executada nesta busca.")
    );
  }

  grade.appendChild(ranking);
  debugConteudo.appendChild(grade);
}

async function buscar(pergunta) {
  if (!pergunta.trim()) return;

  botao.disabled = true;
  mensagem.textContent = "Buscando...";
  confianca.classList.add("escondido");
  limparResultados();
  debugConteudo.innerHTML = '<p class="dica">Processando...</p>';

  try {
    const resposta = await fetch("/api/busca", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pergunta }),
    });
    const dados = await resposta.json();

    if (!resposta.ok) {
      mensagem.textContent = dados.erro || "Erro ao consultar o servidor.";
      return;
    }

    mensagem.textContent = dados.mensagem;
    mostrarConfianca(dados);
    renderizarCards(dados.resultados || []);
    renderizarDebug(dados);

    if (dados.resultados && dados.resultados.length > 0 && !painelDebug.open) {
      // deixa o painel fechado por padrão; o apresentador decide quando abrir
    }
  } catch (erro) {
    mensagem.textContent =
      "Não foi possível conectar ao servidor. Verifique se ele está rodando.";
    debugConteudo.innerHTML =
      '<p class="dica">Sem conexão com o backend.</p>';
  } finally {
    botao.disabled = false;
  }
}

form.addEventListener("submit", (evento) => {
  evento.preventDefault();
  buscar(input.value);
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    input.value = chip.dataset.pergunta;
    buscar(chip.dataset.pergunta);
  });
});
