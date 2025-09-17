# Gerador de Tabela de Custos de Frete Total Express

Este projeto gera tabelas abrangentes de custos de frete para Total Express consultando sua API SOAP para várias faixas de CEP brasileiro (código postal) e faixas de peso.

## Funcionalidades

- Gera tabelas de custos de frete em formato CSV
- Suporta serviços Standard (STD) e Express (EXP)
- Trata faixas de CEP brasileiro e faixas de peso
- Inclui tratamento de erros e logging
- Respeita limites de taxa da API com atrasos incorporados

## Formato da Tabela

Os arquivos CSV gerados seguem este formato:

```csv
ZipCodeStart,ZipCodeEnd,WeightStart,WeightEnd,AbsoluteMoneyCost,TimeCost
1000001,1099999,1,250,11.08,4
1000001,1099999,251,500,11.44,4
...
```

## Pré-requisitos

- Python 3.7+
- Credenciais da API Total Express (usuário e senha)
- Conexão com internet para chamadas da API

## Instalação

1. Clone ou baixe este repositório
2. Crie um ambiente virtual (recomendado):

```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

## Configuração

1. Copie o template do ambiente e preencha suas credenciais:

```bash
cp env-example.txt .env
# Edite o arquivo .env com suas credenciais reais
```

2. O arquivo `.env` deve conter:

```env
TOTAL_EXPRESS_USERNAME=seu_usuario_api_aqui
TOTAL_EXPRESS_PASSWORD=sua_senha_api_aqui
```

## Uso

### Uso Básico

1. Ative seu ambiente virtual:

```bash
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

2. Execute o script para gerar tabelas de frete para ambos os serviços Standard e Express:

```bash
python generate_shipping_table.py
```

Isso criará dois arquivos CSV abrangentes na pasta `./output/`:
- `output/total_express_standard.csv` - Custos de frete standard (338 entradas cobrindo todos os estados)
- `output/total_express_express.csv` - Custos de frete express (338 entradas cobrindo todos os estados)

**Nota:** O script fará 676 chamadas de API no total (338 por serviço) com atrasos de 1 segundo entre requisições, levando aproximadamente 11 minutos para completar. Certifique-se de que suas credenciais da API são válidas e você tem uma conexão estável com a internet.

### Configuração Personalizada

Você pode modificar o script para:
- Alterar faixas de CEP no método `generate_cep_ranges()`
- Alterar faixas de peso no método `generate_weight_ranges()`
- Ajustar parâmetros da API (dimensões, valor declarado, etc.)
- Alterar nomes dos arquivos de saída

### Uso Avançado

```python
from generate_shipping_table_simple import TotalExpressAPI, ShippingTableGenerator

# Inicializar API
api = TotalExpressAPI('seu_usuario', 'sua_senha')

# Criar gerador
generator = ShippingTableGenerator(api)

# Gerar apenas tabela de frete Standard
generator.generate_table('STD', 'custom_standard.csv')

# Gerar apenas tabela de frete Express
generator.generate_table('EXP', 'custom_express.csv')
```

## Detalhes da Integração com API

- **Endpoint**: `https://edi.totalexpress.com.br/webservice_calculo_frete.php?wsdl`
- **Autenticação**: Autenticação HTTP básica
- **Protocolo**: SOAP 1.1
- **Parâmetros**:
  - `TipoServico`: Tipo de serviço ('STD' ou 'EXP')
  - `CepDestino`: CEP de destino (8 dígitos)
  - `Peso`: Peso em kg (formato brasileiro: "10,00")
  - `ValorDeclarado`: Valor declarado
  - `TipoEntrega`: Tipo de entrega (0)
  - `ServicoCOD`: Pagamento na entrega (false)
  - `Altura`, `Largura`, `Profundidade`: Dimensões da embalagem em cm

## Faixas de CEP Brasileiro

O script inclui **faixas de CEP completas** para **todos os 27 estados brasileiros e territórios**:

### Região Sudeste
- **São Paulo (SP)**: 01000-000 até 19999-999
- **Rio de Janeiro (RJ)**: 20000-000 até 28999-999
- **Espírito Santo (ES)**: 29000-000 até 29999-999
- **Minas Gerais (MG)**: 30000-000 até 39999-999

### Região Nordeste
- **Bahia (BA)**: 40000-000 até 48999-999
- **Sergipe (SE)**: 49000-000 até 49999-999
- **Pernambuco (PE)**: 50000-000 até 56999-999
- **Alagoas (AL)**: 57000-000 até 57999-999
- **Paraíba (PB)**: 58000-000 até 58999-999
- **Rio Grande do Norte (RN)**: 59000-000 até 59999-999
- **Ceará (CE)**: 60000-000 até 63999-999
- **Piauí (PI)**: 64000-000 até 64999-999
- **Maranhão (MA)**: 65000-000 até 65999-999

### Região Norte
- **Pará (PA)**: 66000-000 até 68899-999
- **Amapá (AP)**: 68900-000 até 68999-999
- **Tocantins (TO)**: 77000-000 até 77999-999
- **Rondônia (RO)**: 76800-000 até 76999-999
- **Acre (AC)**: 69900-000 até 69999-999
- **Roraima (RR)**: 69300-000 até 69399-999

### Região Centro-Oeste
- **Distrito Federal (DF)**: 70000-000 até 72799-999
- **Goiás (GO)**: 72800-000 até 76799-999
- **Mato Grosso (MT)**: 78000-000 até 78899-999
- **Mato Grosso do Sul (MS)**: 79000-000 até 79999-999

### Região Sul
- **Paraná (PR)**: 80000-000 até 87999-999
- **Santa Catarina (SC)**: 88000-000 até 89999-999
- **Rio Grande do Sul (RS)**: 90000-000 até 99999-999

**Total: 26 regiões cobrindo todos os estados brasileiros e territórios**

## Faixas de Peso

O script usa estas faixas de peso (em gramas):

- 1-250g
- 251-500g
- 501-750g
- 751-1000g
- 1001-2000g
- 2001-3000g
- 3001-4000g
- 4001-5000g
- 5001-6000g
- 6001-7000g
- 7001-8000g
- 8001-9000g
- 9001-10000g

## Tratamento de Erros

O script inclui tratamento abrangente de erros:

- Falhas de conexão da API
- Respostas inválidas
- Erros de autenticação
- Limitação de taxa com retentativas automáticas
- Logging detalhado para `shipping_table_generator.log`

## Considerações de Performance

- O script inclui atrasos de 1 segundo entre chamadas da API para evitar sobrecarga do servidor
- Para grandes conjuntos de dados, considere executar o script em lotes
- Monitore o arquivo de log para quaisquer erros ou falhas da API

## Solução de Problemas

### Problemas Comuns

1. **Falha na Autenticação**: Verifique suas credenciais da API
2. **Timeout de Conexão**: O servidor da API pode estar lento; o script tentará novamente
3. **CEP Inválido**: Certifique-se de que os CEPs estão no formato correto de 8 dígitos
4. **Limitação de Taxa**: Os atrasos incorporados devem prevenir isso

### Logs

Verifique o arquivo `shipping_table_generator.log` para informações detalhadas sobre:
- Requisições e respostas da API
- Mensagens de erro
- Progresso do processamento

## Integração com WooCommerce

Uma vez que você tenha os arquivos CSV, você pode:

1. Importá-los para seu banco de dados WooCommerce
2. Criar métodos de frete personalizados que usem consulta de tabela ao invés de chamadas da API
3. Implementar mecanismos de cache para melhor performance
4. Configurar atualizações periódicas para atualizar os custos de frete

## Licença

Este projeto é lançado sob a licença GPL-2.0.

## Contribuição

Sinta-se à vontade para enviar issues, solicitações de funcionalidades ou pull requests para melhorar esta ferramenta.

## Aviso Legal

Esta ferramenta não é afiliada oficialmente com Total Express. Use por sua própria conta e risco e certifique-se de cumprir com os termos de serviço da Total Express.
