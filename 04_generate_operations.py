import csv
import random
from datetime import datetime, timedelta
from faker import Faker
import config

# Enforce deterministic generation
random.seed(config.SEED)
Faker.seed(config.SEED)
fake = Faker('pt_BR')

def generate_operations():
    print("Generating Telephones for all Users...")

    # --- PART 1: USUARIO_TELEFONE ---
    with open('usuario_telefone.csv', 'w', newline='', encoding='utf-8') as f_tel:
        w_tel = csv.writer(f_tel)
        w_tel.writerow(['id_usuario', 'telefone'])

        # Since IDs were generated sequentially from 1 to N_ROWS_USUARIO in Phase 1
        for id_usuario in range(1, config.N_ROWS_USUARIO + 1):
            telefone_principal = fake.cellphone_number()
            w_tel.writerow([id_usuario, telefone_principal])

            # 10% chance a user has a second phone number
            if random.random() < 0.10:
                telefone_secundario = fake.phone_number()
                # Ensure no duplicates for the composite PK
                if telefone_secundario != telefone_principal: 
                    w_tel.writerow([id_usuario, telefone_secundario])
                    
            if id_usuario % 50_000 == 0:
                print(f"Processed phones for {id_usuario} users...")

    print(f"\nGenerating {config.N_ATENDENTES} Support Staff...")

    # --- PART 2: ATENDENTE ---
    matriculas_atendentes = []
    
    with open('atendente.csv', 'w', newline='', encoding='utf-8') as f_atend:
        w_atend = csv.writer(f_atend)
        w_atend.writerow(['matricula', 'nome', 'turno_trabalho', 'nivel_acesso'])

        turnos = ['Manhã', 'Tarde', 'Noite', 'Madrugada']
        niveis = ['Nível 1', 'Nível 1', 'Nível 2', 'Supervisor'] # Weighted towards N1

        for i in range(config.N_ATENDENTES):
            # Give staff a distinct 5-digit ID format starting at 50000
            matricula = 50000 + i 
            matriculas_atendentes.append(matricula)

            primeiro_nome = fake.first_name()
            sobrenome = fake.last_name()
            
            # CRITICAL: Format for PostgreSQL composite type (tipo_nome)
            nome_composto = f"({primeiro_nome},{sobrenome})"

            turno = random.choice(turnos)
            nivel = random.choice(niveis)

            w_atend.writerow([matricula, nome_composto, turno, nivel])

    print("\nLoading Purchase History into memory...")

    # --- PART 3: CHAMADO_SUPORTE ---
    # Load the metadata generated in Phase 3
    pedidos_metadata = []
    try:
        with open('_pedidos_metadata.csv', 'r', encoding='utf-8') as f_meta:
            reader = csv.reader(f_meta)
            next(reader) # Skip header
            for row in reader:
                # [id_pedido, id_usuario_cliente, data_compra]
                pedidos_metadata.append({
                    'id_pedido': int(row[0]),
                    'id_cliente': int(row[1]),
                    'data_compra': datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S')
                })
    except FileNotFoundError:
        print("Error: Run Phase 3 to generate _pedidos_metadata.csv first.")
        return

    print(f"Sampling {config.N_CHAMADOS_SUPORTE} orders for support tickets...")
    
    # Uniform sampling without replacement guarantees exactly 4% of orders get flagged
    pedidos_com_problema = random.sample(pedidos_metadata, config.N_CHAMADOS_SUPORTE)

    with open('chamado_suporte.csv', 'w', newline='', encoding='utf-8') as f_chamado:
        w_chamado = csv.writer(f_chamado)
        w_chamado.writerow(['protocolo', 'data_abertura', 'assunto', 'descricao', 'status', 'matricula_atendente', 'id_usuario_cliente', 'id_pedido'])

        assuntos = [
            'Dúvida sobre reembolso', 
            'Erro no pagamento', 
            'Alteração de titularidade', 
            'Não recebi o e-mail de confirmação', 
            'Problema no check-in',
            'Dúvida sobre a plataforma online'
        ]
        status_opcoes = ['Aberto', 'Em Andamento', 'Resolvido', 'Cancelado']
        
        # Heavily weight towards resolved tickets to simulate a historical database
        pesos_status = [0.05, 0.10, 0.80, 0.05]

        for index, pedido in enumerate(pedidos_com_problema):
            protocolo = index + 1
            
            # The support ticket must open AFTER the purchase (1 hour to 14 days later)
            horas_atraso = random.randint(1, 336)
            data_abertura = pedido['data_compra'] + timedelta(hours=horas_atraso)

            assunto = random.choice(assuntos)
            descricao = fake.text(max_nb_chars=150).replace('\n', ' ')
            status = random.choices(status_opcoes, weights=pesos_status)[0]
            
            # Assign ticket to a random staff member
            atendente = random.choice(matriculas_atendentes)

            w_chamado.writerow([
                protocolo, 
                data_abertura.strftime('%Y-%m-%d %H:%M:%S'), 
                assunto, 
                descricao, 
                status, 
                atendente, 
                pedido['id_cliente'], 
                pedido['id_pedido']
            ])

            if protocolo % 5_000 == 0:
                print(f"Generated {protocolo} / {config.N_CHAMADOS_SUPORTE} support tickets...")

    print("\nPhase 4 complete! All tables are now fully populated and constrained.")

if __name__ == "__main__":
    generate_operations()