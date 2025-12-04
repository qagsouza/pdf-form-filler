# Como Adicionar Labels aos Campos de Formulário no LibreOffice

## Contexto

O sistema agora suporta a extração e exibição de labels/tooltips dos campos de formulário PDF. Quando um campo PDF contém a propriedade `/TU` (tooltip/user text), o sistema exibirá esse texto descritivo em vez do nome técnico do campo.

## Como configurar no LibreOffice Writer

### Opção 1: Usando Tooltips (Dica de Ferramenta)

1. **Criar o formulário no LibreOffice Writer**
   - Exiba a barra de ferramentas de formulários: Menu → Ver → Barras de ferramentas → Controles de formulário

2. **Adicionar campos de formulário**
   - Insira campos de texto, caixas de seleção, etc.

3. **Adicionar tooltips aos campos**
   - Clique com o botão direito no campo
   - Selecione "Propriedades do controle"
   - Na aba "Geral", procure por:
     - **"Dica"** ou **"Texto de ajuda"** ou **"Tooltip"**
   - Digite o label descritivo desejado

4. **Exportar como PDF**
   - Menu → Arquivo → Exportar como PDF
   - Na janela de exportação, certifique-se de marcar:
     - ☑ "Criar formulário PDF"
     - ☑ "Exportar campos de formulário automaticamente"

### Opção 2: Usando PDF Forms do LibreOffice Draw

O LibreOffice Draw pode ter mais opções para configurar propriedades avançadas de formulários PDF.

### Opção 3: Editar o PDF depois de exportar

Se o LibreOffice não exportar os tooltips, você pode usar ferramentas como:
- **PDFtk** (linha de comando)
- **Adobe Acrobat** (pago)
- **PDF-XChange Editor** (gratuito/pago)
- **Foxit PDF Editor**

Para adicionar a propriedade `/TU` manualmente aos campos.

## Verificando se os labels foram exportados

Use o script de inspeção incluído no projeto:

```bash
python inspect_pdf_fields.py seu_arquivo.pdf
```

Procure pela propriedade `/TU` na saída. Se aparecer, os labels foram exportados com sucesso!

## Exemplo de saída esperada

Com labels:
```
Field #1: nome_completo
  Properties:
    /T: nome_completo
    /TU: Nome Completo do Interessado  ← Label/tooltip
    /FT: /Tx
```

Sem labels:
```
Field #1: nome_completo
  Properties:
    /T: nome_completo
    /FT: /Tx
```

## Como o sistema exibe os labels

### Com label definido:
- **Label principal**: "Nome Completo do Interessado"
- Badge azul pequeno: `nome_completo` (nome técnico)
- Texto auxiliar abaixo: `nome_completo`

### Sem label:
- **Label principal**: `nome_completo` (nome técnico)
- Sem badge adicional

## Benefícios

✅ Formulários mais amigáveis ao usuário
✅ Separação entre nome técnico e descrição legível
✅ Melhor documentação dos campos
✅ Mantém compatibilidade com PDFs sem labels
