Quero criar, no VS Code com auxílio do Codex, um aplicativo desktop em Python para extrair texto e estrutura de arquivos PDF de uma pasta utilizando **Docling com OCR habilitado**.

O aplicativo deverá ser simples de instalar e usar, mas suficientemente organizado e robusto para uso real.

## OBJETIVO

O programa deverá permitir ao usuário:

1. selecionar uma pasta contendo arquivos PDF;
2. localizar automaticamente todos os arquivos `.pdf` dessa pasta;
3. processar os PDFs com Docling;
4. utilizar OCR para PDFs digitalizados ou páginas sem camada textual adequada;
5. extrair o conteúdo estruturado;
6. converter o resultado para Markdown;
7. salvar um arquivo `.md` correspondente a cada PDF;
8. acompanhar o andamento do processamento por uma interface gráfica.

Exemplo:

```text
entrada/
    processo1.pdf
    processo2.pdf
    documento_digitalizado.pdf
```

Resultado:

```text
entrada/
    saida_docling/
        processo1.md
        processo2.md
        documento_digitalizado.md
```

A pasta `saida_docling` deverá ser criada automaticamente.

---

## TECNOLOGIAS

Utilize:

- Python 3
- Tkinter para a interface gráfica
- pathlib para manipulação de caminhos
- threading para processamento em segundo plano
- Docling para leitura e conversão dos PDFs
- OCR integrado ao pipeline do Docling

Evite dependências desnecessárias.

Não utilize framework web.

---

## DOCLING

Utilize a API atual do Docling.

A implementação deve se basear preferencialmente em:

```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
```

Configure um pipeline para PDF com OCR habilitado.

Estrutura esperada:

```python
pipeline_options = PdfPipelineOptions()

pipeline_options.do_ocr = True
pipeline_options.do_table_structure = True

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pipeline_options
        )
    }
)
```

Antes de implementar, verifique a versão instalada do Docling e adapte apenas o necessário caso a API tenha mudado.

Não utilize APIs depreciadas.

---

## OCR

O OCR deve ser efetivamente habilitado.

Prefira inicialmente o mecanismo de OCR integrado ao Docling que exija menos configuração externa.

Se existirem várias opções disponíveis na versão instalada, utilize uma solução que:

- funcione bem com documentos em português;
- dispense instalação manual de executáveis externos, quando possível;
- seja compatível com Windows;
- seja adequada para documentos jurídicos digitalizados.

Configure português como idioma prioritário do OCR, ou português + inglês se isso for tecnicamente mais adequado.

O OCR deverá funcionar mesmo em PDFs compostos exclusivamente por imagens.

Evite depender de Tesseract externo, salvo se isso for realmente necessário.

Se alguma dependência adicional for obrigatória, documente claramente a instalação.

---

## ESTRATÉGIA DE OCR

Quero uma solução confiável.

Não presuma que todo PDF possui camada textual adequada.

O aplicativo deve processar PDFs textuais e PDFs digitalizados.

Se o Docling permitir OCR apenas quando necessário, prefira essa abordagem.

Caso isso complique excessivamente a implementação ou gere comportamento inconsistente, mantenha OCR habilitado para todos os PDFs.

Priorize previsibilidade e qualidade da extração.

---

## INTERFACE GRÁFICA

Use Tkinter.

A janela principal deverá ter o título:

```text
Extrator de PDFs com Docling + OCR
```

Ela deverá conter:

- campo mostrando a pasta selecionada;
- botão `Selecionar pasta`;
- botão `Processar PDFs`;
- botão `Abrir pasta de saída`;
- quantidade de PDFs encontrados;
- nome do arquivo atualmente processado;
- barra de progresso;
- área de log;
- resumo final do processamento.

A interface deve ser simples, limpa e funcional.

---

## SELEÇÃO DA PASTA

Utilize:

```python
tkinter.filedialog.askdirectory
```

Após a seleção, procure arquivos:

```python
*.pdf
```

diretamente na pasta.

Nesta primeira versão, não processe subpastas.

Ordene os PDFs alfabeticamente.

Mostre imediatamente algo como:

```text
12 arquivos PDF encontrados.
```

---

## PROCESSAMENTO

Crie uma única instância do `DocumentConverter` e reutilize-a em todos os documentos.

Não faça:

```python
for pdf in pdfs:
    converter = DocumentConverter(...)
```

Faça algo equivalente a:

```python
converter = criar_converter()

for pdf in pdfs:
    result = converter.convert(pdf)
```

A inicialização dos modelos pode ser custosa e não deve ser repetida.

Para cada PDF:

```python
result = converter.convert(pdf_path)
markdown = result.document.export_to_markdown()
```

Salve o resultado em:

```text
saida_docling/<nome_original>.md
```

utilizando UTF-8.

Exemplo:

```python
output_path.write_text(markdown, encoding="utf-8")
```

---

## THREADING

O processamento do Docling e do OCR pode ser demorado.

Nunca execute o processamento principal diretamente na thread do Tkinter.

Use:

```python
threading.Thread
```

para executar o processamento em segundo plano.

Use:

```python
root.after(...)
```

ou mecanismo equivalente para atualizar widgets do Tkinter com segurança.

Durante o processamento:

- desabilite `Selecionar pasta`;
- desabilite `Processar PDFs`;
- impeça início de um segundo processamento;
- mantenha a interface responsiva.

Ao final, habilite novamente os controles.

---

## PROGRESSO

A barra de progresso deverá representar o número de PDFs concluídos.

Exemplo:

```text
3 / 15
```

Não tente estimar o percentual interno do OCR se o Docling não fornecer isso de forma confiável.

Mostre também o arquivo atual:

```text
Processando 3 de 15:
processo_001.pdf
```

---

## LOG

Crie uma área de log rolável.

Exemplo:

```text
Pasta selecionada:
C:\Processos\PDF

15 PDFs encontrados.

Inicializando Docling e OCR...
Docling inicializado.

[1/15] Processando processo_001.pdf
OK: processo_001.md

[2/15] Processando processo_002.pdf
OK: processo_002.md

[3/15] Processando processo_003.pdf
ERRO: <mensagem>

...

Processamento concluído.
Sucesso: 14
Erros: 1
```

Adicione timestamps apenas se isso não complicar desnecessariamente o código.

---

## TRATAMENTO DE ERROS

Um erro em um PDF não pode interromper o lote inteiro.

Cada documento deve ser tratado individualmente:

```python
try:
    ...
except Exception as e:
    ...
```

Registre o erro no log e continue para o arquivo seguinte.

Ao final, apresente:

- total de PDFs;
- processados com sucesso;
- quantidade de erros;
- pasta de saída.

---

## RELATÓRIO DE ERROS

Além do log da interface, se houver falhas, crie opcionalmente:

```text
saida_docling/erros.txt
```

com uma linha por documento com erro.

Exemplo:

```text
processo_003.pdf | Failed to process document
processo_010.pdf | OCR error
```

Não crie o arquivo se não houver erros.

---

## ARQUIVOS EXISTENTES

Se o arquivo Markdown de destino já existir, não quero confirmação individual.

Adote uma destas estratégias:

preferencialmente:

```text
sobrescrever automaticamente
```

ou, se houver razão técnica forte, implemente opção simples na interface.

A solução padrão deve permanecer simples.

---

## BOTÃO PARA ABRIR A SAÍDA

Implemente um botão:

```text
Abrir pasta de saída
```

que abra `saida_docling` no gerenciador de arquivos do sistema.

Como o ambiente principal será Windows, utilize uma solução compatível com Windows, mas procure manter compatibilidade razoável com macOS e Linux sem adicionar dependências.

---

## ESTRUTURA DO PROJETO

Quero uma organização simples.

Sugestão:

```text
extrator_docling/
│
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

Evite dividir o código em muitos módulos nesta primeira versão.

Se `app.py` ficar excessivamente grande, você pode separar apenas responsabilidades claramente justificadas, por exemplo:

```text
extrator_docling/
│
├── app.py
├── docling_service.py
├── requirements.txt
├── README.md
└── .gitignore
```

Não crie camadas, interfaces abstratas, repositories, controllers ou padrões arquiteturais desnecessários.

---

## REQUIREMENTS

Crie um `requirements.txt` mínimo.

Inclua apenas pacotes realmente necessários.

Não inclua bibliotecas da standard library, como:

- tkinter
- pathlib
- threading
- os
- subprocess

Verifique o pacote correto do Docling na versão atual.

---

## README

Crie um `README.md` curto contendo:

1. objetivo do programa;
2. requisitos;
3. criação de ambiente virtual;
4. instalação;
5. execução;
6. funcionamento do OCR;
7. observação de que a primeira execução pode baixar ou inicializar modelos;
8. estrutura dos arquivos de saída;
9. possíveis limitações.

Inclua comandos para Windows PowerShell.

Exemplo:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

---

## AMBIENTE VIRTUAL

Considere que estou trabalhando no VS Code no Windows.

Utilize `.venv` como nome padrão.

Oriente também a selecionar o interpretador correto no VS Code caso necessário.

---

## QUALIDADE DO CÓDIGO

O código deve:

- ser legível;
- ter nomes de funções claros;
- evitar duplicação;
- ter funções pequenas quando isso melhorar a compreensão;
- usar `pathlib.Path`;
- não utilizar caminhos absolutos;
- ter tratamento de exceções;
- manter a interface separada da lógica pesada de processamento na medida necessária;
- evitar abstrações prematuras.

Use type hints quando ajudarem, mas não transforme o projeto em um exercício de tipagem.

---

## CODIFICAÇÃO

Utilize UTF-8.

Os documentos podem conter:

- acentos;
- nomes próprios;
- símbolos jurídicos;
- caracteres especiais.

Não normalize ou altere desnecessariamente o conteúdo extraído pelo Docling.

---

## FOCO EM DOCUMENTOS JURÍDICOS

Os PDFs processados serão frequentemente documentos jurídicos, como:

- inquéritos policiais;
- processos judiciais;
- denúncias;
- sentenças;
- acórdãos;
- laudos;
- documentos digitalizados.

Por isso, preserve ao máximo:

- títulos;
- parágrafos;
- enumerações;
- tabelas;
- ordem textual;
- separação entre blocos.

Não faça resumo ou interpretação do conteúdo.

A função do programa é exclusivamente extrair e converter o documento.

---

## PRIVACIDADE

Todo o processamento deve ocorrer localmente.

O aplicativo não deve:

- enviar PDFs para serviços externos;
- utilizar APIs remotas;
- enviar conteúdo para LLMs;
- armazenar documentos em nuvem;
- executar telemetria criada por nós.

Se alguma dependência do Docling puder utilizar serviço remoto opcional, não habilite esse recurso.

---

## FUNCIONALIDADES QUE NÃO DEVEM SER IMPLEMENTADAS AGORA

Não implemente nesta versão:

- LLM;
- resumo automático;
- classificação de documentos;
- banco de dados;
- pesquisa semântica;
- embeddings;
- RAG;
- upload para nuvem;
- processamento recursivo de diretórios;
- drag-and-drop;
- edição do Markdown;
- processamento paralelo de vários PDFs;
- instalador executável;
- autenticação;
- servidor web.

Podemos acrescentar funcionalidades posteriormente.

---

## VALIDAÇÃO

Depois de criar a aplicação:

1. revise os imports;
2. verifique se a API utilizada corresponde à versão instalada do Docling;
3. execute o programa;
4. corrija erros de importação ou incompatibilidade;
5. teste com pelo menos:
   - um PDF textual;
   - um PDF digitalizado;
6. confirme a criação dos arquivos `.md`;
7. confirme que a interface não congela durante o processamento;
8. confirme que erro em um PDF não interrompe os demais.

Não considere o trabalho concluído apenas porque o código foi escrito.

Faça os testes possíveis no ambiente local.

---

## FORMA DE TRABALHO COM O CODEX

Você está trabalhando diretamente no projeto dentro do VS Code.

Portanto:

- crie e edite os arquivos necessários;
- execute comandos no terminal quando necessário;
- instale dependências no `.venv`;
- teste a aplicação;
- leia mensagens de erro;
- corrija os problemas encontrados;
- evite pedir que eu faça manualmente algo que você consegue executar;
- não faça alterações fora da pasta do projeto;
- não apague arquivos sem necessidade.

Se encontrar incompatibilidade entre este prompt e a versão atual do Docling, investigue a API instalada e implemente a solução equivalente mais simples.

Ao final, explique objetivamente:

1. quais arquivos foram criados;
2. como executar;
3. como funciona o pipeline PDF → OCR → Docling → Markdown;
4. eventuais limitações conhecidas;
5. melhorias que poderiam ser implementadas numa próxima versão.

Comece examinando o diretório atual do projeto e, em seguida, implemente a primeira versão funcional completa.