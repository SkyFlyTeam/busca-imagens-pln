# Resultados da avaliação

Perguntas de teste **novas**, que não estão no catálogo de referência.

- Total de perguntas: **139**
- Acurácia geral: **100.0%**
- Acurácia em perguntas normais: **100.0%**
- Acurácia com erro de digitação: **100.0%**
- Acerto no rejeite de perguntas fora do domínio: **100.0%**
- Taxa de fallback: **7.9%**

## Acurácia por intenção

| Intenção | Acertos | Total | Acurácia |
|---|---|---|---|
| categorias_disponiveis | 3 | 3 | 100% |
| contar_ano | 5 | 5 | 100% |
| contar_categoria | 7 | 7 | 100% |
| contar_categoria_ano | 3 | 3 | 100% |
| contar_categoria_origem | 5 | 5 | 100% |
| contar_categoria_origem_ano | 3 | 3 | 100% |
| contar_data | 3 | 3 | 100% |
| contar_mes | 4 | 4 | 100% |
| contar_origem | 6 | 6 | 100% |
| contar_origem_ano | 3 | 3 | 100% |
| contar_por_categoria | 2 | 2 | 100% |
| contar_por_origem | 2 | 2 | 100% |
| contar_total | 7 | 7 | 100% |
| listar_ano | 5 | 5 | 100% |
| listar_categoria | 6 | 6 | 100% |
| listar_categoria_ano | 6 | 6 | 100% |
| listar_categoria_origem | 6 | 6 | 100% |
| listar_categoria_origem_ano | 7 | 7 | 100% |
| listar_data | 5 | 5 | 100% |
| listar_mes | 3 | 3 | 100% |
| listar_origem | 6 | 6 | 100% |
| listar_origem_ano | 5 | 5 | 100% |
| listar_todas | 6 | 6 | 100% |
| mais_antigas | 4 | 4 | 100% |
| mais_recentes | 9 | 9 | 100% |
| origens_disponiveis | 7 | 7 | 100% |

## Confusões

Nenhuma confusão.

## Erros detalhados

Nenhum erro.

## Ablação (contribuição de cada etapa)

| Configuração | Acurácia (domínio) |
|---|---|
| Sistema completo (com regras) | 100.0% |
| Sem regras de entidades | 86.7% |
| Sem normalização | 86.7% |
| Sem stopwords | 74.2% |
| Sem stemming | 87.5% |
| Sem substituição de números | 73.4% |
| Sem canonização de sinônimos | 57.8% |
| Sem corretor ortográfico | 82.8% |
| Sem TF-IDF (BOW puro) | 86.7% |

## Curva do limiar

| Limiar | Acurácia geral | Acurácia domínio | Fallback | OOD rejeitado |
|---|---|---|---|---|
| 0.10 | 100.0% | 100.0% | 7.9% | 100.0% |
| 0.15 | 100.0% | 100.0% | 7.9% | 100.0% |
| 0.20 | 100.0% | 100.0% | 7.9% | 100.0% |
| 0.25 | 100.0% | 100.0% | 7.9% | 100.0% |
| 0.30 | 100.0% | 100.0% | 7.9% | 100.0% |
| 0.35 | 100.0% | 100.0% | 7.9% | 100.0% |
| 0.40 | 100.0% | 100.0% | 7.9% | 100.0% |
| 0.45 | 100.0% | 100.0% | 7.9% | 100.0% |
| 0.50 | 100.0% | 100.0% | 7.9% | 100.0% |
| 0.60 | 99.3% | 99.2% | 8.6% | 100.0% |

## Conclusão

O limiar escolhido foi **0.30**, que mantém boa acurácia no domínio e rejeita perguntas fora do domínio. A tabela acima permite justificar a escolha com números.
