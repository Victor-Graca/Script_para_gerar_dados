# Gerador de Dados - Eventosbr

Este projeto é um pipeline de geração de dados sintéticos para a plataforma de venda de ingressos **Eventosbr**. Ele gera milhares de registros correlacionados (Usuários, Eventos, Transações e Operações) e os exporta em arquivos CSV prontos para importação em um Banco de Dados Relacional (PostgreSQL).

## Requisitos e Instalação

A maioria das bibliotecas utilizadas (`csv`, `random`, `datetime`, `subprocess`, `sys`, `time`) são nativas do Python. 

A única dependência externa é a biblioteca **Faker**, utilizada para gerar nomes, endereços, e-mails e frases de forma realista e localizada.

Para instalar, execute no seu terminal:

```bash
pip install Faker
```

## Como Executar

Para iniciar a geração, basta executar o arquivo main.py:

```bash
python main.py
```

O script vai executar todas as fases na ordem correta, garantindo que as dependências de chaves estrangeiras sejam respeitadas.

## Configuração da quantidade de dados gerados

A configuração da quantidade de dados gerados é centralizada no arquivo config.py.

Se desejar gerar mais ou menos dados, basta alterar as variáveis base, como N_ROWS_CLIENTE. O próprio sistema calculará as proporções lógicas para o restante das entidades (eventos, lotes, pedidos e chamados). O arquivo também define uma SEED (padrão 42) para garantir a total reprodutibilidade dos cenários de teste.

## Como o Pipeline Funciona

O projeto é dividido em 4 fases isoladas, que se comunicam através de arquivos temporários de metadados (_meta.csv):

    Fase 1: Usuários (01_generate_users.py)

        Gera a carga base de usuarios, clientes e organizadores.

    Fase 2: Eventos (02_generate_events.py)

        Vincula organizadores a novos eventos (presenciais e online).

        Cria uma linha do tempo lógica de vendas e estabelece a capacidade máxima dos lotes de ingressos.

    Fase 3: Transações (03_generate_transactions.py)

        Simula compras conectando clientes aos eventos.

        Consome os estoques dos lotes e gera múltiplos ingressos por pedido de forma aleatória, calculando valores totais e métodos de pagamento.

    Fase 4: Operações (04_generate_operations.py)

        Gera telefones para os usuários, atendentes com níveis de acesso variados e chamados_suporte atrelados a um percentual dos pedidos gerados na Fase 3.