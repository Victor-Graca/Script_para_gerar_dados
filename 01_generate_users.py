import csv
import random
from faker import Faker
import config

# Set deterministic seeds for reproducible benchmarks
random.seed(config.SEED)
Faker.seed(config.SEED)

fake = Faker('pt_BR')

def generate_unique_cpfs(n_cpfs):
    """Generates N mathematically valid and strictly unique CPFs instantly."""
    bases = random.sample(range(1, 999_999_999), n_cpfs)
    cpfs = []
    for base in bases:
        base_str = f"{base:09d}"
        
        sum1 = sum(int(base_str[i]) * (10 - i) for i in range(9))
        rem1 = sum1 % 11
        dv1 = 0 if rem1 < 2 else 11 - rem1
        
        sum2 = sum(int(base_str[i]) * (11 - i) for i in range(9)) + (dv1 * 2)
        rem2 = sum2 % 11
        dv2 = 0 if rem2 < 2 else 11 - rem2
        
        cpfs.append(f"{base_str[:3]}.{base_str[3:6]}.{base_str[6:9]}-{dv1}{dv2}")
    return cpfs

def generate_unique_cnpjs(n_cnpjs):
    """Generates N mathematically valid and strictly unique CNPJs instantly."""
    bases = random.sample(range(1, 99_999_999), n_cnpjs)
    cnpjs = []
    for base in bases:
        base_str = f"{base:08d}0001"
        
        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum1 = sum(int(base_str[i]) * weights1[i] for i in range(12))
        rem1 = sum1 % 11
        dv1 = 0 if rem1 < 2 else 11 - rem1
        
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        base_str_dv1 = base_str + str(dv1)
        sum2 = sum(int(base_str_dv1[i]) * weights2[i] for i in range(13))
        rem2 = sum2 % 11
        dv2 = 0 if rem2 < 2 else 11 - rem2
        
        cnpjs.append(f"{base_str[:2]}.{base_str[2:5]}.{base_str[5:8]}/{base_str[8:12]}-{dv1}{dv2}")
    return cnpjs

def generate_base_entities():
    print(f"Generating {config.N_ROWS_CLIENTE} clients and {config.N_ROWS_ORGANIZADOR} organizers...")
    
    # 1. Pre-calculate unique documents instantly to avoid Faker's .unique memory trap
    print("Pre-calculating unique CPFs and CNPJs...")
    pool_cpfs = generate_unique_cpfs(config.N_ROWS_CLIENTE)
    pool_cnpjs = generate_unique_cnpjs(config.N_ROWS_ORGANIZADOR)
    
    iter_cpfs = iter(pool_cpfs)
    iter_cnpjs = iter(pool_cnpjs)
    
    # 2. Create and shuffle the blueprint for realistic data interleaving
    blueprint = ['C'] * config.N_ROWS_CLIENTE + ['O'] * config.N_ROWS_ORGANIZADOR
    random.shuffle(blueprint)

    # 3. Open all files simultaneously using context managers
    with open('usuario.csv', 'w', newline='', encoding='utf-8') as f_usuario, \
         open('cliente.csv', 'w', newline='', encoding='utf-8') as f_cliente, \
         open('organizador.csv', 'w', newline='', encoding='utf-8') as f_organizador, \
         open('_cliente_meta.csv', 'w', newline='', encoding='utf-8') as f_c_meta, \
         open('_organizador_ids.csv', 'w', newline='', encoding='utf-8') as f_o_ids:

        # Set up CSV writers
        w_usuario = csv.writer(f_usuario)
        w_cliente = csv.writer(f_cliente)
        w_organizador = csv.writer(f_organizador)
        w_c_meta = csv.writer(f_c_meta)
        w_o_ids = csv.writer(f_o_ids)

        # Write Headers
        w_usuario.writerow(['id_usuario', 'nome', 'email'])
        w_cliente.writerow(['id_usuario', 'cpf', 'data_nascimento'])
        w_organizador.writerow(['id_usuario', 'cnpj', 'razao_social'])
        w_c_meta.writerow(['id_usuario', 'nome', 'cpf'])
        w_o_ids.writerow(['id_usuario'])

        # 4. Stream data directly to disk (Highly memory efficient)
        for index, user_type in enumerate(blueprint):
            id_usuario = index + 1
            
            # --- USUARIO DATA ---
            nome = fake.name()
            # Guarantee unique emails by appending the ID to the username
            username = fake.user_name()
            email = f"{username}_{id_usuario}@{fake.free_email_domain()}"
            
            w_usuario.writerow([id_usuario, nome, email])

            # --- SUB-TYPE ROUTING ---
            if user_type == 'C':
                # Cliente
                cpf = next(iter_cpfs) # Pulls strictly unique CPF instantly
                data_nasc = fake.date_of_birth(minimum_age=16, maximum_age=85).strftime('%Y-%m-%d')
                
                w_cliente.writerow([id_usuario, cpf, data_nasc])
                w_c_meta.writerow([id_usuario, nome, cpf]) 
                
            else:
                # Organizador
                cnpj = next(iter_cnpjs) # Pulls strictly unique CNPJ instantly
                razao_social = fake.company()
                
                w_organizador.writerow([id_usuario, cnpj, razao_social])
                w_o_ids.writerow([id_usuario])

            # Progress indicator 
            if id_usuario % 50_000 == 0:
                print(f"Processed {id_usuario} / {config.N_ROWS_USUARIO} records...")

    print("Generation complete! All CSV files saved to disk.")

if __name__ == "__main__":
    generate_base_entities()