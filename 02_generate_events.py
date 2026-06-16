import csv
import random
from datetime import timedelta
from faker import Faker
import config

# Use the same seed for reproducibility across the pipeline
random.seed(config.SEED)
Faker.seed(config.SEED)
fake = Faker('pt_BR')

def generate_events():
    print(f"Loading {config.N_ROWS_ORGANIZADOR} organizers...")
    
    # 1. Load Organizer IDs from previous step
    organizador_ids = []
    try:
        with open('_organizador_ids.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader) # Skip header
            organizador_ids = [int(row[0]) for row in reader]
    except FileNotFoundError:
        print("Error: Run the user generation script first to create _organizador_ids.csv")
        return

    print(f"Generating {config.N_ROWS_EVENTOS} events ({config.N_PRESENCIAL} Presencial, {config.N_ONLINE} Online)...")

    # 2. Create and shuffle the event type blueprint
    blueprint_eventos = ['P'] * config.N_PRESENCIAL + ['O'] * config.N_ONLINE
    random.shuffle(blueprint_eventos)

    # 3. Open all files
    with open('evento.csv', 'w', newline='', encoding='utf-8') as f_evento, \
         open('presencial.csv', 'w', newline='', encoding='utf-8') as f_presencial, \
         open('online.csv', 'w', newline='', encoding='utf-8') as f_online, \
         open('cadastra.csv', 'w', newline='', encoding='utf-8') as f_cadastra, \
         open('lote.csv', 'w', newline='', encoding='utf-8') as f_lote, \
         open('_lotes_metadata.csv', 'w', newline='', encoding='utf-8') as f_meta:

        # Set up writers
        w_evento = csv.writer(f_evento)
        w_presencial = csv.writer(f_presencial)
        w_online = csv.writer(f_online)
        w_cadastra = csv.writer(f_cadastra)
        w_lote = csv.writer(f_lote)
        w_meta = csv.writer(f_meta)

        # Write Headers (Matching your DDL exactly)
        w_evento.writerow(['id_evento', 'titulo', 'descricao', 'data_hora_inicio', 'data_hora_fim'])
        w_presencial.writerow(['id_evento', 'capacidade_maxima', 'endereco'])
        w_online.writerow(['id_evento', 'plataforma', 'url'])
        w_cadastra.writerow(['id_usuario_organizador', 'id_evento'])
        w_lote.writerow(['id_evento', 'id_lote', 'nome', 'quantidade_total', 'data_limite_venda', 'preco'])
        
        # Metadata Header for the next script
        w_meta.writerow(['id_evento', 'id_lote', 'quantidade_total', 'preco', 'inicio_vendas', 'limite_venda'])

        # 4. Generate the Data
        for index, tipo_evento in enumerate(blueprint_eventos):
            id_evento = index + 1
            
            # --- CADASTRA (Link to an Organizer) ---
            id_organizador = random.choice(organizador_ids)
            w_cadastra.writerow([id_organizador, id_evento])

            # --- EVENTO TIMELINE (The Constraints) ---
            # Sales started sometime in the last 2 years
            inicio_vendas = fake.date_time_between(start_date='-2y', end_date='now')
            
            # Event happens 30 to 180 days AFTER sales start
            dias_ate_evento = random.randint(30, 180)
            data_hora_inicio = inicio_vendas + timedelta(days=dias_ate_evento)
            
            # Event lasts 2 to 8 hours
            horas_duracao = random.randint(2, 8)
            data_hora_fim = data_hora_inicio + timedelta(hours=horas_duracao)

            titulo = fake.catch_phrase()
            descricao = fake.text(max_nb_chars=200)

            # Format for PostgreSQL TIMESTAMP
            w_evento.writerow([
                id_evento, titulo, descricao, 
                data_hora_inicio.strftime('%Y-%m-%d %H:%M:%S'), 
                data_hora_fim.strftime('%Y-%m-%d %H:%M:%S')
            ])

            # --- SUB-TYPES & CAPACITY MATH ---
            capacidade_maxima = 0
            
            if tipo_evento == 'P':
                # Presencial: Strict physical capacity
                capacidade_maxima = random.randint(100, 2000)
                endereco = fake.address().replace('\n', ', ')
                w_presencial.writerow([id_evento, capacidade_maxima, endereco])
            else:
                # Online: Effectively unlimited, but we cap at a high number for the simulation math
                capacidade_maxima = random.randint(5000, 15000)
                plataformas = ['Zoom', 'Microsoft Teams', 'Google Meet', 'YouTube Live']
                w_online.writerow([id_evento, random.choice(plataformas), fake.url()])

            # --- LOTES (Batches) ---
            # Lote 1: 40% of tickets, Cheaper, Ends halfway to the event
            qtd_lote1 = int(capacidade_maxima * 0.4)
            preco_base = round(random.uniform(30.0, 150.0), 2)
            limite_lote1 = inicio_vendas + timedelta(days=(dias_ate_evento // 2))

            w_lote.writerow([id_evento, 1, 'Lote 1 - Early Bird', qtd_lote1, limite_lote1.strftime('%Y-%m-%d'), preco_base])
            w_meta.writerow([id_evento, 1, qtd_lote1, preco_base, inicio_vendas.strftime('%Y-%m-%d %H:%M:%S'), limite_lote1.strftime('%Y-%m-%d %H:%M:%S')])

            # Lote 2: 60% of tickets, More expensive, Ends when event starts
            qtd_lote2 = capacidade_maxima - qtd_lote1
            preco_lote2 = round(preco_base * 1.5, 2)
            limite_lote2 = data_hora_inicio # Sales stop when event starts

            w_lote.writerow([id_evento, 2, 'Lote 2 - Geral', qtd_lote2, limite_lote2.strftime('%Y-%m-%d'), preco_lote2])
            w_meta.writerow([id_evento, 2, qtd_lote2, preco_lote2, limite_lote1.strftime('%Y-%m-%d %H:%M:%S'), limite_lote2.strftime('%Y-%m-%d %H:%M:%S')])

            if id_evento % 5000 == 0:
                print(f"Processed {id_evento} / {config.N_ROWS_EVENTOS} events...")

    print("Generation complete! Metadata pipeline ready for the transactions phase.")

if __name__ == "__main__":
    generate_events()