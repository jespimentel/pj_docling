# Extrator de PDFs com Docling + OCR

Aplicativo desktop local, feito em Python e Tkinter, que transforma os PDFs de uma pasta em arquivos Markdown estruturados. Ele usa o pipeline de PDF do Docling com OCR e extração de tabelas habilitados, priorizando português.

## Requisitos

- Windows 10/11 (também há suporte básico para macOS e Linux)
- Python 3.10 ou superior instalado e disponível no PATH
- Espaço em disco e conexão na primeira execução para o Docling baixar/inicializar os modelos locais necessários

Os PDFs não são enviados pelo aplicativo a serviços externos: a conversão e o OCR acontecem localmente. O eventual acesso à internet é apenas o download inicial de dependências/modelos do Docling.

## Instalação no Windows (PowerShell)

No diretório do projeto, crie e ative o ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação, execute somente nesta sessão:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

No VS Code, use `Ctrl+Shift+P` → `Python: Select Interpreter` e selecione o interpretador em `.venv`.

## Execução

Depois de instalar as dependências, a forma mais simples no Windows é dar duplo clique em `executar.bat`. O arquivo usa automaticamente o Python da pasta `.venv` e mantém a janela aberta caso ocorra um erro.

Também é possível executar pelo PowerShell:

```powershell
python app.py
```

Se `executar.bat` informar que o ambiente virtual está inválido, reinstale o Python e recrie a `.venv` (os comandos de instalação acima). Isso normalmente ocorre quando a instalação do Python usada para criar a `.venv` foi removida ou atualizada.

1. Clique em **Selecionar pasta**.
2. O programa encontra e ordena apenas os arquivos `.pdf` que estão diretamente nela.
3. Clique em **Processar PDFs** e acompanhe o arquivo atual, a barra de progresso e o log.
4. Os resultados são salvos em `saida_docling` dentro da pasta escolhida. Arquivos Markdown existentes com o mesmo nome são sobrescritos sem confirmação.

Exemplo de saída:

```text
entrada/
├── processo1.pdf
└── saida_docling/
    └── processo1.md
```

Quando algum arquivo falha, os outros continuam sendo processados e `saida_docling/erros.txt` é criado com uma linha por falha.

## OCR e limitações

O pipeline mantém OCR e reconhecimento de estrutura de tabelas habilitados. Ele usa o RapidOCR por meio do Docling, com modelo local em português e sem depender do executável externo do Tesseract. Isso atende tanto PDFs com texto incorporado quanto PDFs digitalizados, embora OCR de documentos de baixa resolução, manuscritos, carimbos ou páginas inclinadas possa precisar de revisão humana.

A primeira execução pode demorar mais, pois os modelos do Docling podem ser baixados e inicializados. Processar documentos jurídicos extensos também exige bastante memória e tempo. Esta versão não percorre subpastas nem processa vários PDFs simultaneamente.
