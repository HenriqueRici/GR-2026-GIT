# GR 2026

Processamento da Gratificação por Resultados: carrega SIGABI, Google Sheets e
arquivos WebPonto, identifica elegibilidade e cargos, calcula os eixos e exporta
`PreviaGR.xlsx` e `baseTurmasServidor.xlsx`.

## Executar no Windows / VS Code

Use Python 3.12 ou 3.13 e pandas 2.2/2.3. No terminal PowerShell, dentro do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:SIGABI_LOGIN = "SEU_LOGIN"
$env:SIGABI_SENHA = "SUA_SENHA_ATUAL"
.\.venv\Scripts\python.exe Main.py
```

As variáveis acima valem para a sessão do terminal. Não grave a senha no código
nem em arquivos versionados. A senha presente na versão anterior deve ser
substituída no sistema: retirá-la do arquivo atual não a elimina do histórico Git.

Mantenha a conta de serviço com acesso à planilha **BASES GR 2026** e à pasta
WebPonto. Os caminhos padrão das chaves continuam sendo:

- `google_sheets/credenciais.json`;
- `google_drive/credenciais.json`.

Também é possível informar caminhos externos por `GOOGLE_SHEETS_CREDENTIALS` e
`GOOGLE_DRIVE_CREDENTIALS`. As chaves e os arquivos de dados estão no `.gitignore`.
O projeto não carrega arquivos `.env` automaticamente.

A pasta de saída continua sendo `Path.home() / 'Desktop' / 'GR 2026'` e precisa
existir. A execução sobrescreve as duas planilhas de saída. Guarde uma cópia da
prévia anterior antes de executar. As leituras Google são iniciadas no primeiro
uso, não ao importar o módulo. `set_df` continua sendo uma operação explícita de
substituição de aba e não é chamada pelo fluxo principal.

## Organização

| Arquivo | Responsabilidade |
| --- | --- |
| `Main.py` | `carregar_bases`, `calcular_gr` e ponto de entrada `main` |
| `configuracao.py` | Filtros, campos e conversões das consultas originais |
| `modelos/grupoEleitos.py` | Elegibilidade, vacâncias, classificação e proporção |
| `modelos/metaAdm.py` | Regras dos seis eixos e cálculo vetorizado |
| `modelos/metaAprendizagem.py` | Notas ponderadas e pontuação de aprendizagem |
| `modelos/absenteismo.py` | Ocorrências, dias únicos, JSON e pontuação |
| `modelos/formacao.py` | Distribuição das horas e pontuação de formação |
| `modelos/evasaoEscolar.py` | Frequência e pontuação de evasão |
| `modelos/pontuacao.py` | Pontuação geral e valor final |
| `modelos/conversoes.py` | Conversões numéricas e textuais compartilhadas |
| `modelos/carregamentoDeDados.py` | Arquivos locais e endpoints de formação |
| `modelos/tratamentoPagamento.py` | Exportador legado de pagamento, desativado no Main |
| `sigabi/`, `google_sheets/`, `google_drive/` | Integrações com as fontes |
| `tests/` | Comparações diferenciais e respostas remotas simuladas |

Todas as funções de produção têm docstrings em português. Foram mantidos os
nomes públicos existentes para permitir reaproveitamento das chamadas.

## Compatibilidade e escolhas preservadas

A referência é o commit `948ebdaba9bccf955f7dad2a252697d6ccc8c4c9`.
Esta refatoração não revisa ou valida juridicamente as regras da GR.

- Mesmos filtros de consulta, valores por carreira, faixas, reajustes e ordem de
  operações financeiras. O divisor de 302 dias e as datas de 2026 foram mantidos.
- Mesma ordem e seleção de colunas, deduplicações, arredondamentos e exportações.
- Formação permanece zerada no fluxo principal. Ativá-la seria uma alteração
  funcional e exige bases e decisão próprias.
- O exportador de pagamento mantém o diretório e o corte legados de 2025; não foi
  ativado nem atualizado silenciosamente para 2026.
- Funções de domínio ainda podem modificar argumentos recebidos, conforme o
  comportamento anterior. Use cópias se precisar conservar as entradas.
- Correção explícita: `absenteismoWebPonto` aceita tanto `Func/Vinc` quanto
  `NumFunc/NumVinc`. O Main original passava o primeiro formato para uma função
  que exigia o segundo e falhava com `KeyError`.
- Mudanças operacionais: credenciais SIGABI via ambiente, autenticação Sheets sob
  demanda e importação de `Main` sem executar consultas ou gerar arquivos.

O Drive mantém a política anterior de listar uma página (até 1.000 arquivos) e
continuar após erros individuais. Conversões de data, inclusive suas diferenças
entre fontes, foram preservadas. Entradas vazias, malformadas e chaves ausentes
não receberam um tratamento geral novo; alguns caminhos legados ainda falham
nessas condições. Não interprete execução concluída como auditoria da qualidade
das bases. Esses comportamentos devem ser tratados separadamente, pois mudanças
podem alterar quais registros entram no cálculo.

## Verificação

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python scripts/benchmark_meta.py
```

Os testes carregam o código anterior diretamente do Git. Clone com histórico;
em clone raso, obtenha o commit de referência antes de testar. Não são necessárias
credenciais, dados pessoais ou conexões aos sistemas para a suíte.

Há comparações exatas de DataFrames, tipos, índices, valores, mutações de entrada,
exportações simuladas, consultas, paginação e autenticação. O teste integrado
aplica à referência somente o adaptador explícito de nomes de vínculo do
WebPonto, permitindo comparar os cálculos até a prévia final.

Para validar na sua máquina, execute as versões sobre **o mesmo conjunto congelado
de bases**. Consultas feitas em horários diferentes podem trazer alterações dos
sistemas e não demonstram regressão do código. Compare as prévias preservadas:

```powershell
python scripts/comparar_previas.py PreviaGR_anterior.xlsx PreviaGR_nova.xlsx
```

A suíte sintética não substitui a homologação com as bases completas de produção.
A automação GitHub Actions configura Python 3.12/3.13 e pandas 2.2.3/2.3.2.

## Otimizações

O cálculo administrativo deixou de executar seis `apply(axis=1)` por servidor e
passou a calcular por coluna e cargo. Vacâncias são indexadas por vínculo,
formações por CPF e ocorrências de absenteísmo por vínculo, evitando buscas
repetidas na base inteira. Limites de datas usam máscaras vetorizadas e o valor
final usa aritmética de colunas. Tabelas de aprendizagem e regras dos eixos foram
centralizadas; filtros de entrada e conversões deixaram de ficar espalhados.

O benchmark mede somente os seis eixos em 40 mil registros sintéticos, confere
igualdade exata e informa a mediana de três execuções. Não representa o tempo
completo do sistema, que depende principalmente das fontes e dos arquivos.

### Resultado da validação desta refatoração

No ambiente de validação (Python 3.12.14), os **23 testes passaram** tanto com
pandas **2.2.3** quanto com **2.3.2**. Ruff e compilação também passaram. Python
3.13 está configurado na matriz de CI, mas não foi executado localmente.

Benchmark local com pandas 2.2.3: mediana **1,0171 s → 0,0380 s** para os seis
eixos de 40.000 registros (**26,8×** nessa etapa). Os DataFrames foram comparados
exatamente em cada repetição. O resultado depende do ambiente e não estima o
ganho do processamento completo.
