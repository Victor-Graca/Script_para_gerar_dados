import csv
import random
from datetime import datetime, timedelta
from faker import Faker
import config

# Use the same seed for reproducibility across the pipeline
random.seed(config.SEED)
Faker.seed(config.SEED)
fake = Faker('pt_BR')

def generate_transactions():
    print("Loading Client Metadata into memory (This takes a few seconds)...")
    
    # 1. Load the in-memory dictionary for O(1) lookups
    clientes_dict = {}
    try:
        with open('_cliente_meta.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader) # Skip header
            for row in reader:
                clientes_dict[int(row[0])] = (row[1], row[2])
    except FileNotFoundError:
        print("Error: Run 01_generate_users.py first.")
        return

    lista_id_clientes = list(clientes_dict.keys())

    print("Loading Lotes Metadata into memory...")
    
    # 2. Load Lotes into memory so we can randomly sample them
    lotes_ativos = []
    with open('_lotes_metadata.csv', 'r', encoding='utf-8') as f_meta_in:
        reader_lotes = csv.reader(f_meta_in)
        next(reader_lotes)
        for row in reader_lotes:
            lotes_ativos.append({
                'id_evento': int(row[0]),
                'id_lote': int(row[1]),
                'estoque': int(row[2]),
                'preco': float(row[3]),
                'inicio': datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S'),
                'fim': datetime.strptime(row[5], '%Y-%m-%d %H:%M:%S')
            })

    print(f"Targeting exactly {config.N_PEDIDOS} Pedidos. Starting generation...")

    global_id_pedido = 1
    global_id_ingresso = 1

    # 3. Open the output files
    with open('pedido.csv', 'w', newline='', encoding='utf-8') as f_pedido, \
         open('ingresso.csv', 'w', newline='', encoding='utf-8') as f_ingresso, \
         open('_pedidos_metadata.csv', 'w', newline='', encoding='utf-8') as f_ped_meta:

        w_pedido = csv.writer(f_pedido)
        w_ingresso = csv.writer(f_ingresso)
        w_ped_meta = csv.writer(f_ped_meta)

        w_pedido.writerow(['id_pedido', 'data_compra', 'valor_total', 'metodo_pagamento', 'status', 'id_usuario_cliente'])
        w_ingresso.writerow(['id_ingresso', 'nome_titular', 'cpf_titular', 'status_check_in', 'id_pedido', 'id_evento_lote', 'id_lote'])
        w_ped_meta.writerow(['id_pedido', 'id_usuario_cliente', 'data_compra'])

        metodos_pagamento = ['Cartão de Crédito', 'PIX', 'Boleto']
        status_ingresso = ['Realizado', 'Não Realizado']

        # 4. Target-Driven Loop (Runs exactly config.N_PEDIDOS times)
        while global_id_pedido <= config.N_PEDIDOS:
            
            # Pick a random Lote
            lote = random.choice(lotes_ativos)
            
            ingressos_no_pedido = random.randint(1, 4)
            
            # Prevent overselling the Lote
            if lote['estoque'] < ingressos_no_pedido:
                ingressos_no_pedido = lote['estoque']
                
            # If the Lote is completely sold out, remove it from active rotation
            if ingressos_no_pedido == 0:
                # Fast $O(1)$ list removal: swap with last element and pop
                idx = lotes_ativos.index(lote)
                lotes_ativos[idx] = lotes_ativos[-1]
                lotes_ativos.pop()
                continue
                
            lote['estoque'] -= ingressos_no_pedido

            # --- GENERATE PEDIDO ---
            id_comprador = random.choice(lista_id_clientes)
            nome_comprador, cpf_comprador = clientes_dict[id_comprador]
            
            # Optimized Date Math: Instant calculation instead of relying on Faker
            delta_seconds = int((lote['fim'] - lote['inicio']).total_seconds())
            random_seconds = random.randint(0, delta_seconds)
            data_compra = lote['inicio'] + timedelta(seconds=random_seconds)
            
            valor_total = round(ingressos_no_pedido * lote['preco'], 2)
            metodo = random.choice(metodos_pagamento)
            status_pedido = 'Aprovado' if random.random() < 0.95 else random.choice(['Cancelado', 'Reembolsado'])

            w_pedido.writerow([global_id_pedido, data_compra.strftime('%Y-%m-%d %H:%M:%S'), valor_total, metodo, status_pedido, id_comprador])
            w_ped_meta.writerow([global_id_pedido, id_comprador, data_compra.strftime('%Y-%m-%d %H:%M:%S')])

            # --- GENERATE INGRESSOS FOR THIS PEDIDO ---
            for i in range(ingressos_no_pedido):
                if i == 0:
                    nome_titular = nome_comprador
                    cpf_titular = cpf_comprador
                else:
                    nome_titular = fake.name()
                    # A fast dummy CPF format since DDL doesn't enforce strict validity on friends
                    cpf_titular = f"{random.randint(100,999)}.{random.randint(100,999)}.{random.randint(100,999)}-{random.randint(10,99)}"
                
                status_checkin = random.choices(status_ingresso, weights=[0.85, 0.15])[0] if status_pedido == 'Aprovado' else 'Não Realizado'

                w_ingresso.writerow([
                    global_id_ingresso, nome_titular, cpf_titular, status_checkin, 
                    global_id_pedido, lote['id_evento'], lote['id_lote']
                ])
                
                global_id_ingresso += 1

            # Console tracker now updates based on Pedidos generated
            if global_id_pedido % 50_000 == 0:
                print(f"Generated {global_id_pedido} / {config.N_PEDIDOS} Pedidos...")

            global_id_pedido += 1

    print(f"Generation complete! Created {global_id_pedido - 1} Pedidos and {global_id_ingresso - 1} Ingressos.")

if __name__ == "__main__":
    generate_transactions()