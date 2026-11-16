# Radar de Notícias: Delivery

TP da Aula 8: agente de curadoria de notícias com tool calling (Python, Gemini e Google News RSS).

O programa cria um site com as notícias que o Google News RSS devolve para o pedido, de acordo com o tema que pedimos. O recorte que escolhi foi o de delivery, com paleta em vermelho.

## 1. Preparação do ambiente

Testado no Windows, com PowerShell. Execute um comando por vez.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação, libere só para a janela atual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Configuração da chave, sem colocar nenhuma chave real em arquivo versionado:

1. Copie `.env.example` para `.env`.
2. No `.env`, troque `COLE SUA CHAVE DE API DO GEMINI AQUI` pela sua chave do Gemini. O `.env` está no `.gitignore` e não entra na entrega.
3. `GEMINI_MODEL` define o modelo. Confira qual modelo a sua conta acessa antes de usar (veja a seção 2).

Execução:

```powershell
python agente_noticias.py
python testes_locais.py
```

Logo no início do código, caso não encontre a chave do Gemini, sai com o código 1 no return do if e o programa registra o erro.

## 2. Modelo e versões efetivamente usados

| Item | Versão |
|---|---|
| Sistema | Windows (PowerShell) |
| Python | 3.14.10 |
| Modelo (`GEMINI_MODEL`) | `gemini-3.5-flash-lite` |
| google-genai | 2.34.0 |
| requests | 2.34.2 |
| feedparser | 6.0.14 (traz `feedparser-sgmllib` 2.1.0) |
| python-dotenv | 1.2.4 |

O modelo foi escolhido a partir da lista de modelos que a chave da conta enxergava em 13/11/2026 (consulta à API, sem imprimir a chave). Descartei os modelos de voz, imagem e música, os de pré-visualização (`preview`) e os apelidos `-latest`.

Em nenhum dos testes houve erros relacionados à conta ou à API do Gemini.

## 3. O que mudou e como a paleta foi escolhida

### 3.1 O que mudou no programa

- Nova paleta `delivery` no dicionário `PALETAS`.
- O `INSTRUCOES` passou a descrever quando usar cada paleta, inclusive a nova.
- O retorno da busca guarda a consulta já sem espaços nas pontas (`consulta.strip()`).
- Logs com marcadores `SUCESSO`, `CANCELADO` e `INCOMPLETO`.
- A resposta da função ao modelo usa `types.FunctionResponse` no lugar de `Part.from_function_response(**...)` (ver seção 6.4).
- Arquivo `testes_locais.py` com 23 testes.


### 3.2 Como a paleta foi escolhida

Cores, na ordem fundo, superfície, texto e destaque:

```python
"delivery": ("#240000", "#5f0202", "#eeeded", "#ff8a80")
```

Contrastes calculados pela regra WCAG (alvo: 4,5:1 ou mais):

| Par | Contraste |
|---|---|
| texto sobre fundo | 16,7:1 |
| texto sobre superfície | 12,0:1 |
| destaque sobre superfície | 6,1:1 |
| destaque sobre fundo | 8,6:1 |

O destaque original era `#bc0606`, com contraste de apenas 2,1:1 sobre a superfície dos cards. Ele foi clareado para `#ff8a80`, mantendo o vermelho, para os links e a fonte ficarem legíveis.

A paleta de delivery segue a associação mais comum que empresas de FastFood seguem, colocando o vermelho no fundo com um destaque mais claro para facilitar a legibilidade, sem perder o foco dos tons avermelhados.

## 4. As ferramentas e o papel do estado


- `buscar_noticias`: faz a consulta escolhida pelo modelo, validando que esteja dentro do limite entre 2 e 180. Depois de conseguir a resposta no google news, verifica se o conteúdo da resposta passa de 2 mb. Para cada entrada que passar pelo filtro(título, https, host exato, sem duplicata) presente no feed, adiciona na lista de notícias o dicionário contendo id, titulo, link, fonte e data.

- `criar_site`: recebe tema e paleta para começar a renderização do site, usando as quatro cores da paleta escolhida no CSS do dicionário PALETAS para utilizar. Para cada noticia dentro do dicionário de dados["noticias"], é adicionado um card com escape para proteger contra possíveis tags de script.

A ferramenta não é responsável por saber quais notícias entram. Se o modelo recebesse a lista como argumento, ele poderia reescrever o título errado, inventar uma fonte ou trocar o link (alucinação). Também gastaria mais token reenviando a lista inteira e poderia inserir um link malicioso se tivesse lido um título com ordem escondida.


FERRAMENTAS é apenas o que o modelo vê que é nome, descrição e os argumentos. As validações ficam divididas nas funções de `processar_ferramenta`, `renderizar_site` e `buscar_noticias`. 
A função `processar_ferramenta` possui dois caminhos de validação: 

 - `buscar_noticias`: recusa qualquer chamada depois de sucesso ou cancelamento, aceita apenas o argumento consulta, impede que exceda o limite de duas buscas e não permite adicionar novas notícias caso já tenha dados recuperados.

 - `criar_site`: recusa qualquer chamada depois de sucesso ou cancelamento, aceita somente os argumentos de tema e paleta, garante que o tema esteja entre 2 a 120 caracteres, valida se a paleta informada está no dicionário de PALETAS, verifica se tem notícias dentro da lista de dados e só salva a criação caso seja confirmada pelo usuário ao digitar S ou s (o strip() tira os espaços, enquanto o lower() deixa minúscula).



## 5. Logging, contexto e arquivos persistidos


- **Logging:** Funciona para informar ou avisar o usuário de forma mais limpa o que aconteceu durante a criação. O log só aparece em terminal e não fica salvo em arquivo nenhum.
- **Contexto (`conversa`):** é a lista de mensagens (pedido, respostas do modelo, resultados das ferramentas) que o programa reenvia a cada rodada, e só existe na memória do programa durante a execução.
- **Arquivos persistidos:** `index.html` é a página criada para mostrar as notícias recuperadas pelo pedido de busca do modelo. O `noticias.json` é a lista onde se encontram essas notícias recuperadas, armazenando consulta, coletado_em, seus metadados (id, titulo, link, fonte e data) e ao final de todas as notícias, a urlfeed utilizada. Já o `historico.json` armazena as ferramentas que foram utilizadas, em qual rodada foi utilizada, qual foi o retorno dela e só é salvo no sucesso.

## 6. Resultados

### 6.1 Testes locais

```powershell
python testes_locais.py
```

Resultado: 23 testes, todos `ok` (saída completa em `saida_testes.txt`).

Os testes locais **não** verificam a conexão com o Gemini, o RSS real nem a aparência visual. Todos os dados usados neles são fictícios, escritos à mão, e não são notícias recuperadas ao vivo. O feed dos testes de filtro é um XML montado à mão, lido no lugar da internet. Os testes das responsabilidades de cada função auxiliaram para que o código funcionasse sem a necessidade de fazer integrações para verificar cada tipo de resposta e retorno.

Os testes cobrem cada validação presente no código original, garantindo que o programa retorne as exceções certas quando houver erro ou retorne a mensagem certa quando tudo for bem executado. 

### 6.2 Os quatro cenários

Execuções reais com o modelo `gemini-3.5-flash-lite`, feitas em 13/11/2026. O cenário 1 foi repetido em 15/11/2026 para registrar o log (ver abaixo).

| # | Cenário | Pedido | Consulta escolhida pelo modelo | Paleta | Resultado |
|---|---|---|---|---|---|
| 1a | Seu tema, com autorização (execução original, 13/11) | "notícias sobre delivery de comida e entregadores" (provavelmente; o pedido não foi registrado) | `delivery de comida e entregadores` | `delivery` | SUCESSO, 6 cards. Pasta `sites/20261113_235037_498444`. O log do terminal não foi guardado |
| 1b | Mesmo cenário, repetido para registrar o log (15/11) | "notícias sobre delivery de comida e entregadores" | `delivery de comida e entregadores` | `delivery` | SUCESSO, 6 cards. Pasta `sites/20261115_155733_836835` |
| 2 | Outro recorte | "As últimas notícias de IA relacionadas ao Gemini" | `Google Gemini IA ultimas noticias` | `tecnologia` | SUCESSO, 6 cards. Pasta `sites/20261113_234710_195585` |
| 3 | Cancelamento | "As últimas notícias de IA relacionadas ao gemini" | `gemini IA noticias` | `tecnologia` | CANCELADO. A pasta `sites/20261113_234646_200257` não foi criada |
| 4 | Criação sem notícias | (teste local) | não se aplica | não se aplica | Recusa com `ValueError`, sem pasta criada |

**Cenário 1**: o terminal da execução original (13/11, por volta das 23:50) não foi guardado. A pasta dela, `sites/20261113_235037_498444`, mantém o site, o `noticias.json` e o `historico.json`, e é o site que aparece nas capturas da seção 6.3. O log abaixo é de uma **repetição** feita em 15/11, com o pedido `notícias sobre delivery de comida e entregadores` e a pasta `sites/20261115_155733_836835`.

Log da repetição de 15/11: O modelo começou utilizando a ferramenta de busca e, logo depois, usou a ferramenta de criação escolhendo o tema e a paleta adequados ao pedido, tudo em duas rodadas. O programa só salvou o site após a minha aprovação.

```text
15:57:33 | INFO | Iniciando agente com modelo: gemini-3.5-flash-lite
15:57:34 | INFO | --- Rodada 1 ---
15:57:34 | INFO | HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent "HTTP/1.1 200 OK"
15:57:34 | INFO | Ferramenta solicitada: buscar_noticias | args: {'consulta': 'delivery de comida e entregadores'}
15:57:34 | INFO | Executando busca de notícias para: delivery de comida e entregadores
15:57:35 | INFO | Busca concluída. 6 notícias encontradas.
15:57:35 | INFO | --- Rodada 2 ---
15:57:36 | INFO | HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent "HTTP/1.1 200 OK"
15:57:36 | INFO | Ferramenta solicitada: criar_site | args: {'tema': 'Mercado de Delivery de Comida e Entregadores', 'paleta': 'delivery'}
15:57:36 | INFO | Renderizando site. Tema 'Mercado de Delivery de Comida e Entregadores', Paleta 'delivery'
15:57:36 | INFO | Solicitando autorização para gravar 6 cards.

Autoriza salvar 'Mercado de Delivery de Comida e Entregadores' (paleta: delivery) em sites\20261115_155733_836835? [s/N] s
15:58:05 | INFO | Site gravado: sites\20261115_155733_836835\index.html
15:58:05 | INFO | SUCESSO: abra sites\20261115_155733_836835\index.html
15:58:05 | INFO | Agente encerrado.
```

**Cenário 2** (log):

Assim como no cenário 1, o modelo começou utilizando a ferramenta de busca e, logo depois, usou a ferramenta de criação escolhendo o tema e a paleta adequados ao pedido, tudo em duas rodadas. O programa só salvou o site após a minha aprovação.

```text
Qual site de notícias você quer criar? As últimas notícias de IA relacionadas ao Gemini
23:47:10 | INFO | Iniciando agente com modelo: gemini-3.5-flash-lite
23:47:10 | INFO | --- Rodada 1 ---
23:47:10 | INFO | HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent "HTTP/1.1 200 OK"
23:47:10 | INFO | Ferramenta solicitada: buscar_noticias | args: {'consulta': 'Google Gemini IA ultimas noticias'}
23:47:10 | INFO | Executando busca de notícias para: Google Gemini IA ultimas noticias
23:47:11 | INFO | Busca concluída. 6 notícias encontradas.
23:47:11 | INFO | --- Rodada 2 ---
23:47:12 | INFO | HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent "HTTP/1.1 200 OK"
23:47:12 | INFO | Ferramenta solicitada: criar_site | args: {'paleta': 'tecnologia', 'tema': 'Últimas Notícias e Atualizações do Google Gemini IA'}
23:47:12 | INFO | Renderizando site. Tema 'Últimas Notícias e Atualizações do Google Gemini IA', Paleta 'tecnologia'
23:47:12 | INFO | Solicitando autorização para gravar 6 cards.

Autoriza salvar 'Últimas Notícias e Atualizações do Google Gemini IA' (paleta: tecnologia) em sites\20261113_234710_195585? [s/N] s
23:47:16 | INFO | Site gravado: sites\20261113_234710_195585\index.html
23:47:16 | INFO | SUCESSO: abra sites\20261113_234710_195585\index.html
23:47:16 | INFO | Agente encerrado.
```

**Cenário 3** (log, e a prova de que não houve criação: a pasta `sites/20261113_234646_200257`, mostrada na pergunta de autorização, não existe. `sites/` só contém as três pastas dos cenários 1 (duas execuções) e 2):

O modelo efetuou a busca, solicitou a ferramenta de criar site, mas a criação foi cancelada pelo usuário. Nenhum arquivo foi criado na pasta. O log termina em CANCELADO.

```text
Qual site de notícias você quer criar? As últimas notícias de IA relacionadas ao gemini
23:46:46 | INFO | Iniciando agente com modelo: gemini-3.5-flash-lite
23:46:46 | INFO | --- Rodada 1 ---
23:46:47 | INFO | HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent "HTTP/1.1 200 OK"
23:46:47 | INFO | Ferramenta solicitada: buscar_noticias | args: {'consulta': 'gemini IA noticias'}
23:46:47 | INFO | Executando busca de notícias para: gemini IA noticias
23:46:48 | INFO | Busca concluída. 6 notícias encontradas.
23:46:48 | INFO | --- Rodada 2 ---
23:46:48 | INFO | HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent "HTTP/1.1 200 OK"
23:46:48 | INFO | Ferramenta solicitada: criar_site | args: {'paleta': 'tecnologia', 'tema': 'Atualizações do Gemini IA e Lançamentos Recentes'}
23:46:48 | INFO | Renderizando site. Tema 'Atualizações do Gemini IA e Lançamentos Recentes', Paleta 'tecnologia'
23:46:48 | INFO | Solicitando autorização para gravar 6 cards.

Autoriza salvar 'Atualizações do Gemini IA e Lançamentos Recentes' (paleta: tecnologia) em sites\20261113_234646_200257? [s/N] n
23:46:54 | WARNING | Criação cancelada pelo usuário.
23:46:54 | WARNING | CANCELADO: nenhum site foi gravado nesta execução.
23:46:54 | INFO | Agente encerrado.
```

**Cenário 4**: demonstrado por chamada direta de `processar_ferramenta("criar_site", ...)`, sem depender de o modelo errar. Testes `test_recusa_sem_busca_previa` (estado sem busca) e `test_recusa_lista_vazia` (busca que voltou vazia). Os dois passaram.

Por ser um teste local, não apresenta log do agente nem chamada ao Gemini.

### 6.3 O site: janela larga, janela estreita e teclado

Capturas em `evidencias/`:

- `site_completo.png`: janela larga, cards em colunas.
- `responsivo_celular.png`: largura de 360 px, uma coluna, sem rolagem horizontal.
- `prova_tab.png`: contorno de foco visível em um link após `Tab`.

Apertar a tecla tab no teclado funcionou exatamente como o desejado, bem visível e passou pelos links na ordem dos cards, permitindo apertar enter na notícia em que paramos com o atalho e entrar nela. 

### 6.4 Incidente: erro do `id` na resposta da função

Na primeira execução integrada, depois da busca bem-sucedida, o programa falhou com:

```text
Falha na execução (TypeError): Part.from_function_response() got an unexpected keyword argument 'id'
```

A `google-genai` 2.34.0 não aceita `id` nessa função (a assinatura é `name`, `response`, `parts`). O código da aula passava o `id` por ela. A correção foi montar a resposta com `types.FunctionResponse(name=..., response=..., id=...)`.

Os testes locais não detectariam esse erro, porque não chamam o Gemini. Ele só apareceu na execução integrada.

Testes unitários facilitam muito para verificar o funcionamento das possíveis situações que um usuário pode acabar tendo, mas não garante 100% da qualidade pois não verifica integrações, como por exemplo uma chamada ao Gemini.

## 7. Limitações

- Não lê o texto integral das matérias: o site mostra só metadados do RSS.
- Não verifica fatos: a veracidade do que as fontes dizem não é checada.
- Não implementa MCP.
- Não garante temas totalmente relacionados: na execução de delivery, o feed trouxe notícias sobre a concorrência entre iFood e outras marcas, mas também falou sobre o avanço tecnológico e uma matéria intitulada 'Depressão Charles: serviços de entrega de comida estão quase todos suspensos'.
- O RSS ordena por relevância, não por data, mesmo com "últimas notícias" no pedido.
- O título vem do Google News com o nome da fonte no fim, e o card também mostra a fonte, então a informação aparece duas vezes.
- O limite de 2 MB do feed é conferido depois do download completo, então protege o processamento, não o download.
- Se a gravação do `historico.json` falhar depois do site gravado, o programa sai com erro apesar do site existir.
- O modelo varia entre execuções (consultas e temas diferentes para pedidos parecidos).
- Os testes locais não cobrem o laço do `main` (cinco rodadas, desfechos e códigos de saída), nem o comportamento do modelo.
- Tokens, latência e custo não são medidos.

## 8. Estrutura da entrega

```text
agente_noticias.py
testes_locais.py
saida_testes.txt
requirements.txt
.env.example
.gitignore
README.md
evidencias/            (capturas)
testes_auxiliares/     (rascunhos usados, ver abaixo)
sites/
  20261113_234710_195585/   (cenário 2)
  20261113_235037_498444/   (cenário 1, execução original, sem log)
  20261115_155733_836835/   (cenário 1, repetição com log)
```

Em `testes_auxiliares/`: `teste_modelos.py` lista os modelos que a chave da conta acessa, sem imprimir a chave, e foi o que usei para escolher o modelo; `teste_render.py` gera uma página de teste com dados fictícios, usada para conferir o escape e o layout.

Não fazem parte da entrega: `.env`, `.venv/`, `__pycache__/` e `saida_teste.html`.
