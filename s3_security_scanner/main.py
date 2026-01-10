import datetime

# --- DADOS MOCK (Simulando a resposta da AWS) ---
aws_s3_buckets = [
    {"Name": "financeiro-dados-sens", "Encryption": "AES256", "Public": False},
    {"Name": "site-estatico-imagens", "Encryption": "None", "Public": True},
    {"Name": "logs-aplicacao-prod", "Encryption": "AWS-KMS", "Public": False},
    {"Name": "backup-antigo-dev", "Encryption": "None", "Public": False}
]

def auditar_bucket(bucket_dados):
    encryption_status = bucket_dados['Encryption']
      
    if encryption_status == "None":
        return False  
    else:
        return True  

def gerar_relatorio():
    
    print(f"--- INICIANDO AUDITORIA S3 [{datetime.date.today()}] ---\n")
    
    buckets_inseguros = 0
    
    for bucket in aws_s3_buckets:
        nome = bucket['Name']
        
        is_secure = auditar_bucket(bucket)
        
        if is_secure == True:
            print(f"[✅ OK] O bucket '{nome}' está encriptado.")
        else:
            print(f"[❌ ALERTA] O bucket '{nome}' NÃO TEM ENCRIPTAÇÃO!")
            buckets_inseguros += 1
            
    print(f"\n--- RESUMO: {buckets_inseguros} buckets vulneráveis encontrados. ---")

if __name__ == "__main__":
    gerar_relatorio()
