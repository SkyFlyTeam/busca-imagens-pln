# Resultados da avaliação

Perguntas de teste **novas**, que não estão no catálogo de referência.

- Total de perguntas: **113**
- Acurácia geral: **100.0%**
- Acurácia em perguntas normais: **100.0%**
- Acurácia com erro de digitação: **100.0%**
- Acerto no rejeite de perguntas fora do domínio: **100.0%**
- Taxa de fallback: **9.7%**

## Acurácia por intenção

| Intenção | Acertos | Total | Acurácia |
|---|---|---|---|
| contar_ano | 5 | 5 | 100% |
| contar_categoria | 6 | 6 | 100% |
| contar_categoria_ano | 3 | 3 | 100% |
| contar_categoria_origem | 5 | 5 | 100% |
| contar_categoria_origem_ano | 3 | 3 | 100% |
| contar_origem | 6 | 6 | 100% |
| contar_origem_ano | 3 | 3 | 100% |
| contar_total | 6 | 6 | 100% |
| listar_ano | 5 | 5 | 100% |
| listar_categoria | 6 | 6 | 100% |
| listar_categoria_ano | 5 | 5 | 100% |
| listar_categoria_origem | 6 | 6 | 100% |
| listar_categoria_origem_ano | 7 | 7 | 100% |
| listar_data | 5 | 5 | 100% |
| listar_origem | 6 | 6 | 100% |
| listar_origem_ano | 5 | 5 | 100% |
| listar_todas | 5 | 5 | 100% |
| mais_antigas | 3 | 3 | 100% |
| mais_recentes | 6 | 6 | 100% |
| origens_disponiveis | 6 | 6 | 100% |

## Confusões

Nenhuma confusão.

## Erros detalhados

Nenhum erro.

## Ablação (contribuição de cada etapa)

| Configuração | Acurácia (domínio) |
|---|---|
| Sistema completo (com regras) | 100.0% |
| Sem regras de entidades | 82.4% |
| Sem normalização | 82.4% |
| Sem stopwords | 71.6% |
| Sem stemming | 82.4% |
| Sem substituição de números | 73.5% |
| Sem canonização de sinônimos | 55.9% |
| Sem corretor ortográfico | 79.4% |
| Sem TF-IDF (BOW puro) | 89.2% |

## Curva do limiar

| Limiar | Acurácia geral | Acurácia domínio | Fallback | OOD rejeitado |
|---|---|---|---|---|
| 0.10 | 100.0% | 100.0% | 9.7% | 100.0% |
| 0.15 | 100.0% | 100.0% | 9.7% | 100.0% |
| 0.20 | 100.0% | 100.0% | 9.7% | 100.0% |
| 0.25 | 100.0% | 100.0% | 9.7% | 100.0% |
| 0.30 | 100.0% | 100.0% | 9.7% | 100.0% |
| 0.35 | 100.0% | 100.0% | 9.7% | 100.0% |
| 0.40 | 100.0% | 100.0% | 9.7% | 100.0% |
| 0.45 | 100.0% | 100.0% | 9.7% | 100.0% |
| 0.50 | 100.0% | 100.0% | 9.7% | 100.0% |
| 0.60 | 100.0% | 100.0% | 9.7% | 100.0% |

## Conclusão

O limiar escolhido foi **0.30**, que mantém boa acurácia no domínio e rejeita perguntas fora do domínio. A tabela acima permite justificar a escolha com números.
